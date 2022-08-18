import datetime
from fastapi import APIRouter
from typing import Optional
from skyfield import api
from skyfield import almanac
router = APIRouter()


@router.get("/sunrise")
def get_sunrise(lat: float,
                lon: float,
                date: str,
                height: Optional[float] = 0):
    """
    Returns moonrise and sunset for a given
    date and position in lat,lon with optional height

    Arguments
    ---------
    lat: float
        latitude in degrees
    lon: float
        longitude in degrees
    date: str
        date on format YYYY-DD-MM
    """
    date = datetime.datetime.strptime(date, '%Y-%d-%m')
    next_day = date + datetime.timedelta(days=1)

    ts = api.load.timescale()
    eph = api.load('de421.bsp')
    loc = api.wgs84.latlon(lat, lon)
    # Find sunset and sunrise
    start = ts.utc(date.year, date.month, date.day, 0)
    end = ts.utc(next_day.year, next_day.month, next_day.day, 0)
    
    sunrise, sunset = set_and_rise(loc, eph, start, end, "Sun")
    moonrise, moonset = set_and_rise(loc, eph, start, end, "Moon")
    solarnoon = meridian_transit(loc, eph, start, end, "Sun")

    data = {}
    data["sunrise"] = sunrise
    data["sunset"] = sunset
    data["moonrise"] = moonrise
    data["moonset"] = moonset
    data["solarnoon"] = solarnoon
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
    return(t.utc_iso())

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
    # Only set if there is 
    # set and rise, else None 
    for ti, yi in zip(t,y):
        if yi:
            rise = ti
        elif not yi:
            set = ti
    
    return(rise, set)