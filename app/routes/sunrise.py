import re
from datetime import datetime, timedelta

from enum import Enum
from fastapi import APIRouter, HTTPException, Query, Path
from typing import Optional
from numpy import where
from skyfield import api
from skyfield.api import utc
from skyfield import almanac
from http import HTTPStatus
from routes.initialize import init_eph
from core.make_response import make_response

AU_TO_KM = 149597871000  # 1 AU in Km
EPS = 0.0001
TIME_FORMAT = "%Y-%m-%dT%H:%M"

router = APIRouter()
eph = init_eph()


class bodies(str, Enum):
    moon: str = "moon"
    sun: str = "sun"


@router.get("/events/{body}")
async def get_sunrise(
    body: bodies = Path(..., description="Celestial body for which to query for events"),
    date: str = Query(...,
                      description="date on format YYYY-MM-DD.",
                      ),
    lat: float = Query(default=51.477, gt=-90.0, lt=90.0,
                       description="latitude in degrees. Default value set to Greenwich observatory."),
    lon: float = Query(default=-0.001, gt=-180.0, lt=180.0,
                       description="longitude in degrees. Default value set to Greenwich observatory."),
    elevation: Optional[float] = Query(default=0,
                                       description="elevation above earth ellipsoid in unit meter."),
    offset: Optional[str] = Query(default="+00:00",
                                  description="Offset from utc time. Has to be on format +/-HH:MM"),
                       ):
    """
    Returns moonrise and sunset for a given
    date and position in (lat,lon) with optional height
    """

    # Capitalize first letter of moon and sun
    body = body.value.capitalize()

    # Regex checking YYYY-MM-DD patter
    pattern = re.compile(r"([12]\d{3}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01]))")
    if not pattern.match(date):
        raise HTTPException(detail="Invalid format for date parameter entered. "
                                   "The date parameter has to be on the form YYYY-MM-DD",
                            status_code=HTTPStatus.BAD_REQUEST)
    # Regex checking +/-HH:MM offset pattern
    offset_pattern = re.compile(r"[+-][0-9]{2}:[0-9]{2}\b")
    if not offset_pattern.match(offset):
        raise HTTPException(detail="Invalid format for offset parameter entered. "
                                   "The date parameter has to be on the form +/-HH:MM",
                            status_code=HTTPStatus.BAD_REQUEST)
    datetime_date = datetime.strptime(date, "%Y-%m-%d")
    ts = api.load.timescale()
    # eph = init_eph()
    global eph
    loc = api.wgs84.latlon(lat, lon, elevation_m=elevation)
    # Parse offset string
    offset_h = int(offset[:3])
    offset_m = int(offset[4:])
    # Make sure minutes is also negative if offset_h is negative
    if offset_h < 0:
        offset_m = -offset_m
    # Offset in solar time. Not "political" Timezone
    delta_offset = - lon / 15

    rising, setting, noon, moonphase, start, end = await calculate_one_day(
        datetime_date,
        ts,
        eph,
        loc,
        offset_h,
        offset_m,
        delta_offset,
        body)
    return (make_response(setting, rising, noon[0], noon[1],
                          start.strftime(TIME_FORMAT),
                          end.strftime(TIME_FORMAT),
                          body, lat, lon, elevation, moonphase, offset))


async def calculate_one_day(date, ts, eph, loc, offset_h,
                            offset_m, delta_offset, body):
    """
    Returns moonrise and sunset for a given
    date and position in lat,lon with optional height

    date: datetime object
        date to calculate for
    ts: skyfield.api ts object
        latitude in degrees.
    eph: skyfield.api ephemeral object
        longitutde in degrees
    loc: skyfield.api.wgs84.latlon object
        (lat,lon) position on Earth
    offset_h: int
        hours of offset from utc
    offset_m: int
        minutes of offset from utc
    delta_offset: float
        offset from utc in solar time (lon/15)
    """

    # Set start and end time for position with UTC offset
    start = datetime(date.year, date.month, date.day, tzinfo=utc)

    start = start + timedelta(hours=delta_offset)
    end = start + timedelta(days=1, minutes=1)
    if body == "Sun":
        noon = await meridian_transit(loc, eph, ts.utc(start), ts.utc(end),
                                      "Sun", offset_h, offset_m, ts)

        # Use solarnoon to set start and end of interval.
        solarnoon_strptime = datetime.strptime(noon[0][0], TIME_FORMAT)
        solarnoon_minus_12h = (solarnoon_strptime
                               - timedelta(hours=12)).replace(tzinfo=utc)
        solarnoon_plus_12_h = (solarnoon_strptime
                               + timedelta(hours=12)).replace(tzinfo=utc)

        start = ts.utc(min(start, solarnoon_minus_12h))
        end = ts.utc(max(end, solarnoon_plus_12_h))
        moonphase = None
    elif body == "Moon":
        start = ts.utc(start)
        end = ts.utc(end)
        noon = await meridian_transit(loc, eph, start, end,
                                      body, offset_h, offset_m, ts)
        moonphase = almanac.moon_phase(eph, start)
    else:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST,
                            detail=f"Unsopported celestial body \"{body}\" entered.")

    rising, setting = await set_and_rise(loc, eph, start, end,
                                         body, offset_h, offset_m)
    return (rising, setting, noon, moonphase,
            start.utc_datetime(), end.utc_datetime())


async def meridian_transit(loc, eph, start, end, body, offset_h, offset_m, ts):
    """
    Calculates the time at which a body passes a location meridian,
    at which point it reaches its highest elevation in the sky

    Arguments:
    ----------
    loc: skyfield.toposlib.GeographicPosition Object
        location of observer given lat, lon in wgs84 projection
        from skyfield api module

    eph: skyfield.jpllib.SpiceKernel Object
        loaded ephemeral table from skyfield api module

    start: Time::TT object
        Date argument converted through skyfield api module

    start: Time::TT object
        The day after date argument converted through skyfield api module

    body: str
        Name of celestial object in which
        to calculate rising and setting times
    ts: skyfield.api timescale Object
        timescale needed for calculating visibility
    """
    f = almanac.meridian_transits(eph, eph[body], loc)
    times, events = almanac.find_discrete(start, end, f, epsilon=EPS)
    astro = (eph["earth"] + loc).at(times).observe(eph[body])
    app = astro.apparent()
    alt, az, distance = app.altaz()
    distance = distance.au
    alt = alt.dstr()
    antimeridian = times[events == 0][0]
    meridian = times[events == 1][0]
    meridian_index = where(events == 1)[0][0]
    antimeridian_index = where(events == 0)[0][0]

    # Check if body is visible to inform about polar day and night
    meridian_visible = f(meridian)
    antimeridian_visible = f(antimeridian)

    antimeridian = antimeridian.utc_datetime() + timedelta(hours=offset_h, minutes=offset_m)
    meridian = meridian.utc_datetime() + timedelta(hours=offset_h, minutes=offset_m)
    meridian_list = [meridian.strftime(TIME_FORMAT), alt[meridian_index],
                     str(distance[meridian_index] * AU_TO_KM) + " km",
                     meridian_visible]
    antimeridian_list = [antimeridian.strftime(TIME_FORMAT), alt[antimeridian_index],
                         str(distance[antimeridian_index] * AU_TO_KM) + " km",
                         antimeridian_visible]
    return (meridian_list, antimeridian_list)


async def set_and_rise(loc, eph, start, end, body, offset_h, offset_m):
    """
    Calculates rising and setting times for a given
    celestial body as viewed from a location on Earth.

    Arguments:
    ----------
    loc: skyfield.toposlib.GeographicPosition Object
        location of observer given lat, lon in wgs84 projection
        from skyfield api module

    eph: skyfield.jpllib.SpiceKernel Object
        loaded ephemeral table from skyfield api module

    start: Time::TT object
        Date argument converted through skyfield api module

    start: Time::TT object
        The day after date argument converted through skyfield api module

    body: str
        Name of celestial object in which
        to calculate rising and setting times
    offset_h: int
        hours of offset from utc
    offset_m: int
        minutes of offset from utc
    """
    # Find set and rise for a celestial body
    # Use specially made function if body == Sun
    # For taking into account atmospheric refraction and sun diameter
    if body == "Sun":
        f = almanac.sunrise_sunset(eph, loc)
    else:
        f = almanac.risings_and_settings(eph, eph[body], loc)
    t, y = almanac.find_discrete(start, end, f, epsilon=EPS)
    if len(y) > 0:
        astro = (eph["earth"] + loc).at(t).observe(eph[body])
        app = astro.apparent()
        alt, az, distance = app.altaz()
        distance = distance.au
        az = az.dstr()
    else:
        az = [None, None]
    t = t.utc_datetime() + timedelta(hours=offset_h, minutes=offset_m)

    set = [None, None]
    rise = [None, None]
    zip_list = list(zip(t, y, az, distance))
    for ti, yi, az, dist in zip_list:
        if yi:
            rise = ti.strftime(TIME_FORMAT)
            rise = [rise, az]
        elif not yi:
            set = ti.strftime(TIME_FORMAT)
            set = [set, az]
    return (rise, set)
