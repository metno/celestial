import datetime
from fastapi import APIRouter, HTTPException, Query, Body
from typing import Optional
from skyfield import api
from skyfield import almanac
from http import HTTPStatus
router = APIRouter()


@router.get("/sunrise")
def get_sunrise(date: str = Query(None, description="date on format YYYY-DD-MM"),
                lat: float = Query(default=51.477, gt=-90.0, lt= 90.0,
                                   description="latitude in degrees. Default value set to Greenwich observatory"),
                lon: float = Query(default= -0.001, gt=-180.0, lt = 180.0,
                                   description="latitude in degrees. Default value set to Greenwich observatory"),
                utc_offset: str = Query(default="+00:00"),
                elevation: Optional[float] = Query(default=0,
                                                  description="elevation above earth ellipsoid")):
    """
    Returns moonrise and sunset for a given
    date and position in lat,lon with optional height
    """
    date = datetime.datetime.strptime(date, '%Y-%d-%m')
    next_day = date + datetime.timedelta(days=1)

    ts = api.load.timescale()
    eph = api.load('de421.bsp')
    loc = api.wgs84.latlon(lat, lon, elevation_m=elevation)
    # Find sunset and sunrise
    start = ts.utc(date.year, date.month, date.day, 0)
    end = ts.utc(next_day.year, next_day.month, next_day.day, 0)
    
    sunrise, sunset = set_and_rise(loc, eph, start, end, "Sun")
    moonrise, moonset = set_and_rise(loc, eph, start, end, "Moon")
    solarnoon = meridian_transit(loc, eph, start, end, "Sun")

    # Create datetime object for utcoffset
    hour_offset = float(utc_offset[1] + utc_offset[2])
    minute_offset = float(utc_offset[4] + utc_offset[5])
    delta = datetime.timedelta(hours=hour_offset,
                               minutes=minute_offset)
    data = {}
    if utc_offset[0] == "+":
        data["sunrise"] = (sunrise + delta) if sunrise is not None else None
        data["sunset"] = (sunset + delta) if sunset is not None else None
        data["moonrise"] = (moonrise + delta) if moonrise is not None else None
        data["moonset"] = (moonset + delta) if moonset is not None else None
        data["solarnoon"] = (solarnoon + delta) if solarnoon is not None else None
    elif utc_offset[0] == "-":
        data["sunrise"] = (sunrise - delta) if sunrise is not None else None
        data["sunset"] = (sunset - delta) if sunset is not None else None
        data["moonrise"] = (moonrise - delta) if moonrise is not None else None
        data["moonset"] = (moonset - delta) if moonset is not None else None
        data["solarnoon"] = (solarnoon + delta) if solarnoon is not None else None
    else:
        raise HTTPException(status_code = HTTPStatus.BAD_REQUEST,
                            detail="First element of utc_offset "
                                   "string argument has to be a plus or "
                                   "minus sign.")
    return(data)

def meridian_transit(loc, eph, start, end, body):
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
    """
    f = almanac.meridian_transits(eph, eph[body], loc)
    
    times, events = almanac.find_discrete(start, end, f)
    times = times[events == 1]
    t = times[0]
    t = t.utc_iso()
    return(datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%SZ"))

def set_and_rise(loc, eph, start, end, body):
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
    """
    # Find set and rise for a celestial body
    f = almanac.risings_and_settings(eph, eph[body], loc)
    t, y = almanac.find_discrete(start, end, f)
    t = t.utc_iso()

    set = None
    rise = None
    # Only use first two elements to account for two day interval
    # Rising or setting may take place the next day.
    zip_list = list(zip(t,y))
    for ti, yi in zip_list[:2]:
        if yi:
            rise = ti
        elif not yi:
            set = ti
    if rise is not None:
        rise = datetime.datetime.strptime(rise, "%Y-%m-%dT%H:%M:%SZ")
    if set is not None:
        set = datetime.datetime.strptime(set, "%Y-%m-%dT%H:%M:%SZ")
    return(rise, set)