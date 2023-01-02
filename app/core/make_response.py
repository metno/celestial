import re
from datetime import datetime, timedelta

def make_response(setting, rising, meridian, antimeridian,
                  start, end, body, lat, lon, altitude,
                  moonphase, offset) -> dict:
    response = {}
    response["copyright"] = "MET Norway"
    response["licenseURL"] = "https://api.met.no/license_data.html"

    response["type"] = "Feature"
    response["geometry"] = {"type": "Point",
                            "coordinates": [lon, lat, altitude]}
    #print(delta_offset)
    #delta_offset_string = datetime.fromtimestamp(3600 * delta_offset).strftime("%H:%M")
    #delta_offset_string = str(timedelta(hours=delta_offset))
    #print(delta_offset_string)
    #sign = "-" if delta_offset > 0 else "+"

    response["when"] = {"interval": [start + "+00:00",
                                     end + "+00:00"]
                        }          
    properties = {}
    properties["body"] = body

    rising_time = rising[0] + offset if rising[0] is not None else None
    az = round(rising[1], 2) if rising[1] is not None else None
    properties[f"{body.lower()}rise"] = {
                                    "time": rising_time,
                                    "azimuth": az
                                    }

    setting_time = setting[0] + offset if setting[0] is not None else None
    az = round(setting[1], 2) if setting[1] is not None else None
    properties[f"{body.lower()}set"] = {
                                "time": setting_time,
                                "azimuth": az
                                }
    events = [None,None]
    if body == "Sun":
        events = ["solarnoon", "solarmidnight"]
    elif body == "Moon":
        events = ["high_moon", "low_moon"]

    properties[events[0]] = {
                             "time": meridian[0] + offset,
                             "disc_centre_elevation": round(meridian[1], 2),
                             "distance": round(float(meridian[2]), 2),
                             "visible": str(meridian[3]) == "True"
                             }

    properties[events[1]] = {
                             "time": antimeridian[0] + offset,
                             "disc_centre_elevation": round(antimeridian[1], 2),
                             "distance": round(float(antimeridian[2]), 2),
                             "visible": str(antimeridian[3]) == "True"
                             }
    if moonphase:
        properties["moonphase"] = {"value": round(moonphase.degrees, 2)}
    response["properties"] = properties
    return (response)
