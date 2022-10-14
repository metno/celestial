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

AU_TO_KM = 149597871000 # 1 AU in Km

router = APIRouter(prefix="/v3")

class format(str, Enum):
    json = ".json"
    xml = ".xml"

@router.get("/{response_format}")
async def get_sunrise(response_format: format = Query(None, description="File format of response."),
                date: str = Query(None,
                                  description="date on format YYYY-MM-DD."),
                lat: float = Query(default=51.477, gt=-90.0, lt= 90.0,
                                   description="latitude in degrees. Default value set to Greenwich observatory."),
                lon: float = Query(default= -0.001, gt=-180.0, lt = 180.0,
                                   description="longitude in degrees. Default value set to Greenwich observatory."),
                elevation: Optional[float] = Query(default=0,
                                                   description="elevation above earth ellipsoid in unit meter."),
                offset: Optional[str] = Query(default="+00:00",
                                              description="Offset from utc time. Has to be on format +/-HH:MM"),
                days: Optional[int]=Query(default=1,
                                          description="Number of days to calculate for.")):
    """
    Returns moonrise and sunset for a given
    date and position in (lat,lon) with optional height
    """
    # Regex checking YYYY-MM-DD pattern
    pattern = re.compile(r"([12]\d{3}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01]))") 
    if not pattern.match(date):
        raise HTTPException(detail="Invalid format for date parameter entered. "
                                   "The date parameter has to be on the form YYYY-MM-DD",
                            status_code=HTTPStatus.BAD_REQUEST)
    # Regex checkign +/-HH:MM offset pattern
    offset_pattern = re.compile(r"[+-][0-9]{2}:[0-9]{2}\b")
    if not offset_pattern.match(offset):
        raise HTTPException(detail="Invalid format for offset parameter entered. "
                                   "The date parameter has to be on the form +/-HH:MM",
                            status_code=HTTPStatus.BAD_REQUEST)
    datetime_date = datetime.strptime(date, "%Y-%m-%d")
    ts = api.load.timescale()
    eph = init_eph()
    loc = api.wgs84.latlon(lat, lon, elevation_m=elevation)
    # Parse offset string
    offset_h = int(offset[:3])
    offset_m = int(offset[4:]) 

    data = {}
    data["height"] = str(elevation)
    data["latitude"] = str(lat)
    data["longitude"] = str(lon)
    data["time"] = []
    
    for i in range(days):
        #time_1 = time.time()
        sunrise, sunset, moonrise, moonset, solarnoon, moonphase = calculate_one_day(datetime_date,
                                                                                     ts,
                                                                                     eph,
                                                                                     loc,
                                                                                     offset_h,
                                                                                     offset_m) 
        #total_time = time.time() - time_1
        #print(f"Total time: {total_time}")
        day_i_element = {}
        day_i_element["date"] = datetime_date.strftime("%Y-%m-%d")
        day_i_element["sunrise"] = {"desc": "LOCAL DIURNAL SUN RISE",
                                    "time": sunrise[0],
                                    "Azimuth:": sunrise[1],
                                    "distance": sunrise[2]}
        day_i_element["sunset"] = {"desc": "LOCAL DIURNAL SUN SET",
                                   "time": sunset[0],
                                   "Azimuth:": sunset[1],
                                   "distance": sunset[2]}
        day_i_element["moonrise"] = {"desc": "LOCAL DIURNAL MOON RISE",
                                     "time": moonrise[0],
                                     "Azimuth:": f"{moonrise[1]}",
                                     "distance": moonrise[2]}
        day_i_element["moonset"] = {"desc": "LOCAL DIURNAL MOON SET",
                                   "time": moonset[0],
                                   "Azimuth:": moonset[1],
                                   "distance": moonset[2]}
        day_i_element["moonphase"] = {"desc": "Moonphase",
                                      "time" : date + "T00:00:00" + offset,
                                      "value": moonphase.degrees}
        day_i_element["solarnoon"] = {"desc": "SOLAR MERIDIAN CROSSING",
                                      "time": solarnoon[0]}
        day_i_element["solarmidnight"] = {"desc": "SOLAR ANTIMERIDIAN CROSSING",
                                          "time": solarnoon[1]}
        data["time"].append(day_i_element)
        datetime_date = datetime_date + timedelta(days=1)
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
        start = ts.utc(start.utc_datetime()
                       + timedelta(hours=offset_h, minutes=offset_m))
        end = ts.utc(end.utc_datetime()
                     + timedelta(hours=offset_h, minutes=offset_m))
    else: 
        start = ts.utc(start.utc_datetime()
                       - timedelta(hours=abs(offset_h), minutes=offset_m))
        end = ts.utc(end.utc_datetime()
                     - timedelta(hours=offset_h, minutes=offset_m))

    #time_1 = time.time()
    sunrise, sunset = set_and_rise(loc, eph, start, end, "Sun", offset_h, offset_m)
    #time_2 = time.time()
    #time_tot_1 = (time_2 - time_1) * 1000
    #print(f"sunrise and sunset time: {time_tot_1} ms")
    #time_1 = time.time()
    moonrise, moonset = set_and_rise(loc, eph, start, end, "Moon", offset_h, offset_m)
    #time_2 = time.time()
    #time_tot_2 = (time_2 - time_1) * 1000
    #print(f"moonrise and moonset time: {time_tot_2} ms")
    #time_1 = time.time()
    solarnoon = meridian_transit(loc, eph, start, end, "Sun", offset_h, offset_m)
    #time_2 = time.time()
    ##time_tot_3 = (time_2 - time_1) * 1000
    ##print(f"Solarnoon time: {time_tot_3} ms")
    #time_1 = time.time()
    moonphase = almanac.moon_phase(eph, start)
    #time_2 = time.time()
    #time_tot_3 = (time_2 - time_1) * 1000
    #print(f"moonphase time: {time_tot_3} ms")
    return(sunrise, sunset, moonrise, moonset, solarnoon, moonphase)


def meridian_transit(loc, eph, start, end, body, offset_h, offset_m):
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
    #print(times)
    antimeridian = times[events==0]
    meridian = times[events == 1]
    meridian = times[0]
    antimeridian = antimeridian[0]
    antimeridian = antimeridian.utc_datetime() + timedelta(hours=offset_h, minutes=offset_m)
    meridian = meridian.utc_datetime() + timedelta(hours=offset_h, minutes=offset_m)
    return(meridian.strftime("%Y-%m-%dT%H:%M"), antimeridian.strftime("%Y-%m-%dT%H:%M"))

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
    # For taking into account atmospheric refraction and sun diameter
    if body == "Sun":
        f = almanac.sunrise_sunset(eph, loc)
    else:
        f = almanac.risings_and_settings(eph, eph[body], loc)
    t, y = almanac.find_discrete(start, end, f)
    if len(y) > 0:
        astro = (eph["earth"] + loc).at(t).observe(eph[body])
        app = astro.apparent()
        alt, az, distance = app.altaz()
        distance = distance.au
        az = az.dstr()
    else:
        az, distance = [None, None], [None, None]

    t = t.utc_datetime() + timedelta(hours=offset_h, minutes=offset_m)
    set = [None, None, None]
    rise = [None, None, None]
    zip_list = list(zip(t, y, az, distance))
    for ti, yi, az, distance in zip_list:
        if yi:
            rise = ti.strftime("%Y-%m-%dT%H:%M")
            rise = [rise, az, str(distance * AU_TO_KM) + " km"]
        elif not yi:
            set = ti.strftime("%Y-%m-%dT%H:%M")
            set = [set, az, str(distance * AU_TO_KM) + " km"]
    return(rise, set)