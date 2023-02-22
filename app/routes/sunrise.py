import re
import schemas.response_schemas as response_schemas
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

EPS = 0.0001
TIME_FORMAT = "%Y-%m-%dT%H:%M"
ATMOSPHERE_REFRAC = 0.5666 # Average angle in which atmospheric refraction moves the horizon
MOON_RADIUS_DEGREES = 0.2667 # Roughly stimated average Moon radius in degrees 

router = APIRouter()
eph = init_eph()


class bodies(str, Enum):
    moon: str = "moon"
    sun: str = "sun"


@router.get("/events/{body}",
            responses={200: {"model": response_schemas.events}})
async def get_sunrise(
    body: bodies = Path(..., description="Celestial body for which to query for events"),
    date: str = Query(...,
                      description="date on format YYYY-MM-DD.",
                      ),
    lat: float = Query(default=51.477, gt=-90.0, lt=90.0,
                       description="latitude in degrees. Default value set to Greenwich observatory."),
    lon: float = Query(default=-0.001, gt=-180.0, lt=180.0,
                       description="longitude in degrees. Default value set to Greenwich observatory."),
    offset: Optional[str] = Query(default="+00:00",
                                  description="Offset from utc time. Has to be on format +/-HH:MM"),
                       ) -> dict:
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
    offset_pattern = re.compile(r"[ +-]\d\d:\d\d")
    if not offset_pattern.match(offset):
        raise HTTPException(detail="Invalid format for offset parameter entered. "
                                   "The date parameter has to be on the form +/-HH:MM",
                            status_code=HTTPStatus.BAD_REQUEST)
    datetime_date = datetime.strptime(date, "%Y-%m-%d")
    ts = api.load.timescale()
    # eph = init_eph()
    global eph
    loc = api.wgs84.latlon(lat, lon)
    # Parse offset string
    offset_h = int(offset[:3])
    offset_m = int(offset[4:])
    # Make sure minutes is also negative if offset_h is negative
    if offset_h < 0:
        offset_m = -offset_m
    # Offset in solar time. Not "political" Timezone
    delta_offset = - lon / 15
    # correct for locations on the "wrong" side of the date line
    if lon > 100 and offset_h < 0:
        # e.g. Attu (172.9, 52.9, UTC-10)
        delta_offset += 24
    elif lon < -100 and offset_h > 0:
        # e.g. Tonga (-175.2, -21.1, UTC+13)
        delta_offset -= 24

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
                          body, lat, lon, moonphase, offset))


async def calculate_one_day(date, ts, eph, loc, offset_h,
                            offset_m, delta_offset, body) -> list:
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
    end = start + timedelta(days=1)
    
    f_transit = almanac.meridian_transits(eph, eph[body], loc)
    if body == "Sun":
        # Add one minute to account for noon occuring at 12:00
        _end = end + timedelta(minutes=1)

        # Use specially made function if body == Sun
        # For taking into account atmospheric refraction and sun diameter
        f_rising = almanac.sunrise_sunset(eph, loc)
        noon = await meridian_transit(loc, eph, ts.utc(start), ts.utc(_end),
                                      "Sun", f_rising,
                                      f_transit)

        # Use solarnoon to set start and end of interval.
        solarnoon_strptime = noon[0][0]
        solarnoon_minus_12h = (solarnoon_strptime
                               - timedelta(hours=12)).replace(tzinfo=utc)
        solarnoon_plus_12_h = (solarnoon_strptime
                               + timedelta(hours=12)).replace(tzinfo=utc)
        start = min(start, solarnoon_minus_12h)
        end = max(end, solarnoon_plus_12_h)
        moonphase = None
    elif body == "Moon":
        f_rising = almanac.risings_and_settings(
            eph, eph[body], loc,
            horizon_degrees=ATMOSPHERE_REFRAC,
            radius_degrees=MOON_RADIUS_DEGREES
        )
        # Add one minute to account for noon occuring at 12:00
        _end = end + timedelta(minutes=1)
        noon = await meridian_transit(loc, eph, ts.utc(start), ts.utc(_end),
                                      body,
                                      f_rising, f_transit)
        moonphase = almanac.moon_phase(eph, ts.utc(start))
    else:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST,
                            detail=f"Unsopported celestial body \"{body}\" entered.")

    # convert noon to string with queried offset.
    noon[0][0] = ((noon[0][0]
        + timedelta(hours=offset_h,
                    minutes=offset_m)).strftime(TIME_FORMAT)
                        if noon[0][0] is not None else None)
    noon[1][0] = ((noon[1][0]
        + timedelta(hours=offset_h,
                    minutes=offset_m)).strftime(TIME_FORMAT)
                        if noon[1][0] is not None else None)

    rising, setting = await set_and_rise(loc, eph, ts.utc(start), ts.utc(end),
                                         body, offset_h, offset_m, f_rising)
    return (rising, setting, noon, moonphase, start, end)


async def meridian_transit(loc, eph, start, end, body,
                           f_rising, f_transit) -> list:
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

    f_rising: skyfield almanac.rising_and_settings object
        Initialized object for finding rising and setting times.
        Used in this function for checking visibility of an object

    f_transit: skyfield almanac.meridian_transits object
        Initialized object for finding meridian transit times.
    """

    times, events = almanac.find_discrete(start, end, f_transit, epsilon=EPS)
    astro = (eph["earth"] + loc).at(times).observe(eph[body])
    app = astro.apparent()
    alt = app.altaz()[0]
    alt = alt.degrees

    try:
        antimeridian = times[events == 0][0]
    except IndexError:
        # Special case where no antimeridian crossing events are found 
        antimeridian_list = [None, None, None]
    else:
        antimeridian_index = where(events == 0)[0][0]
        # Check if body is visible to inform about polar day and night
        antimeridian_visible = f_rising(antimeridian)
        antimeridian_list = [antimeridian.utc_datetime(),
                            alt[antimeridian_index],
                            antimeridian_visible]
    try:
        meridian = times[events == 1][0]
    except IndexError:
        # Special case where no meridian crossing events are found
        meridian_list = [None, None, None]
    else:
        meridian_index = where(events == 1)[0][0]
        meridian_visible = f_rising(meridian)
        meridian_list = [meridian.utc_datetime(),
                        alt[meridian_index],
                        meridian_visible]

    return (meridian_list, antimeridian_list)


async def set_and_rise(loc, eph, start, end,
                       body, offset_h, offset_m, f) -> list:
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

    f: skyfield almanac.rising_and_settings object
        Initialized object for finding rising and setting times.
        Used in this function for checking visibility of an object
    """
    # Find set and rise for a celestial body
    t, y = almanac.find_discrete(start, end, f, epsilon=EPS)
    if len(y) > 0:
        astro = (eph["earth"] + loc).at(t).observe(eph[body])
        app = astro.apparent()
        az = app.altaz()[1]
        az = az.degrees
    else:
        az = [None, None]
    t = t.utc_datetime() + timedelta(hours=offset_h, minutes=offset_m)

    set = [None, None]
    rise = [None, None]
    zip_list = list(zip(t, y, az))
    for ti, yi, az in zip_list:
        if yi:
            rise = ti.strftime(TIME_FORMAT)
            rise = [rise, az]
        elif not yi:
            set = ti.strftime(TIME_FORMAT)
            set = [set, az]
    return (rise, set)
