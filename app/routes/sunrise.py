import re
from datetime import datetime, timedelta
from enum import Enum
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from typing import Optional
from skyfield import api
from skyfield import almanac
from http import HTTPStatus
from routes.initialize import init_eph
from core.make_xml import make_xml
import time

router = APIRouter()


class format(str, Enum):
    xml = ".xml"
    json = ".json"


@router.get("/{response_format}")
async def get_sunrise(response_format: Optional[format] = Query(None, description="File format of response."),
                date: str = Query(None,
                                  description="date on format YYYY-MM-DD."),
                lat: float = Query(default=51.477, gt=-90.0, lt= 90.0,
                                   description="latitude in degrees. Default value set to Greenwich observatory."),
                lon: float = Query(default= -0.001, gt=-180.0, lt = 180.0,
                                   description="longitude in degrees. Default value set to Greenwich observatory."),
                elevation: Optional[float] = Query(default=0,
                                                   description="elevation above earth ellipsoid in unit meter."),
                offset: Optional[str] = Query(default="+00:00",
                                              description="Offset from utc time. Has to be on format +(-)HH:mm"),
                days: Optional[int]=Query(default=1,
                                          description="Number of days to calculate for.")):
    """
    Returns moonrise and sunset for a given
    date and position in (lat,lon) with optional height
    """
    # Regex checking YYYY-MM-DD pattern
    pattern = re.compile(r"([12]\d{3}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01]))") 
    if date is None:
        raise HTTPException(detail="Please enter a value for the date parameter.",
                            status_code=HTTPStatus.BAD_REQUEST)
    elif not pattern.match(date):
        raise HTTPException(detail="Invalid format for date parameter entered. "
                                   "The date parameter has to be on the form YYYY-MM-DD",
                            status_code=HTTPStatus.BAD_REQUEST)

    date = datetime.strptime(date, "%Y-%m-%d")
    ts = api.load.timescale()
    eph = init_eph()
    loc = api.wgs84.latlon(lat, lon, elevation_m=elevation)

    # Parse offset string
    offset_h = int(offset[:3])
    offset_m = int(offset[4:]) 
    #print(int(offset[:3]))
    #print(int(offset[4:]))

    #timezone_obj = TimezoneFinder()
    #timezone_obj = timezone_obj.timezone_at(lng=lon, lat=lat)
    #tz = timezone(timezone_obj)
    data = {}
    data["height"] = str(elevation)
    data["latitude"] = str(lat)
    data["longitude"] = str(lon)
    data["time"] = []

    for i in range(days):
        #time_1 = time.time()
        sunrise, sunset, moonrise, moonset, solarnoon = calculate_one_day(date, ts, eph, loc, offset_h, offset_m)#, tz) 
        #total_time = time.time() - time_1
        #print(f"Total time: {total_time}")
        day_i_element = {}
        day_i_element["date"] = date.strftime("%Y-%m-%d")
        day_i_element["sunrise"] = {"desc": "LOCAL DIURNAL SUN RISE",
                                    "time": sunrise}
        day_i_element["sunset"] = {"desc": "LOCAL DIURNAL SUN SET",
                                   "time": sunset}
        day_i_element["moonrise"] = {"desc": "LOCAL DIURNAL MOON RISE",
                                     "time": moonrise}
        day_i_element["moonset"] = {"desc": "LOCAL DIURNAL MOON SET",
                                   "time": moonset}
        day_i_element["solarnoon"] = {"desc": "LOCAL DIURNAL SOLAR NOON",
                                      "time": solarnoon}
        data["time"].append(day_i_element)
        date = date + timedelta(days=1)
    if response_format == format.xml:
        return(Response(content = make_xml(data), media_type="application/xml"))
    elif response_format == format.json:
        return(data)
    else:
        raise HTTPException(detail=f"Unknown or not supported format requested: {format}.",
                            status_code=HTTPStatus.BAD_REQUEST)



def calculate_one_day(date, ts, eph, loc, offset_h, offset_m):
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
    tz: pytz timezone object
        timezone for a given (lat,lon) position
    offset_h: int
        hours of offset from utc
    offset_m: int
        minutes of offset from utc 
    """
    next_day = date + timedelta(days=1)

    # Set start and end time for position with UTC offset
    start = ts.utc(date.year, date.month, date.day)
    end = ts.utc(next_day.year, next_day.month, next_day.day)
    if offset_h >= 0:
        start = ts.utc(start.utc_datetime() + timedelta(hours=offset_h, minutes=offset_m))
        end = ts.utc(end.utc_datetime() + timedelta(hours=offset_h, minutes=offset_m))
    else: 
        start = ts.utc(start.utc_datetime() - timedelta(hours=abs(offset_h), minutes=offset_m))
        end = ts.utc(end.utc_datetime() - timedelta(hours=offset_h, minutes=offset_m))

    #time_1 = time.time()
    sunrise, sunset = set_and_rise(loc, eph, start, end, "Sun", offset_h, offset_m)
    #time_2 = time.time()
    #time_tot_1 = time_2 - time_1
    #print(f"sunrise and sunset time: {time_tot_1}S")
    #time_1 = time.time()
    moonrise, moonset = set_and_rise(loc, eph, start, end, "Moon", offset_h, offset_m)
    #time_2 = time.time()
    #time_tot_2 = time_2 - time_1
    #print(f"moonrise and moonset time: {time_tot_2}S")
    #time_1 = time.time()
    solarnoon = meridian_transit(loc, eph, start, end, "Sun", offset_h, offset_m)
    #time_2 = time.time()
    #time_tot_3 = time_2 - time_1
    #print(f"Solarnoon time: {time_tot_3}S")
    return(sunrise, sunset, moonrise, moonset, solarnoon)


def meridian_transit(loc, eph, start, end, body, offset_h, offset_m):#, tz):
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
    t = t.utc_datetime() + timedelta(hours=offset_h, minutes=offset_m)
    return(t.strftime("%Y-%m-%dT%H:%M"))

def set_and_rise(loc, eph, start, end, body, offset_h, offset_m):
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
    # Use specially made function if body == Sun
    # For taking into account atmospheric refraction
    if body == "Sun":
        f = almanac.sunrise_sunset(eph, loc)
    else:
        f = almanac.risings_and_settings(eph, eph[body], loc)
    t, y = almanac.find_discrete(start, end, f)
    t = t.utc_datetime() + timedelta(hours=offset_h, minutes=offset_m)
    set = None
    rise = None
    zip_list = list(zip(t,y))
    for ti, yi in zip_list:
        if yi:
            rise = ti.strftime("%Y-%m-%dT%H:%M")
        elif not yi:
            set = ti.strftime("%Y-%m-%dT%H:%M")
    return(rise, set)