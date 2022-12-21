import re

def make_response(setting, rising, meridian, antimeridian,
                  start, end, body, lat, lon, elevation,
                  moonphase, offset) -> dict:
    response = {}
    response["copyright"] = "MET Norway"
    response["licenseURL"] = "https://api.met.no/license_data.html"

    response["type"] = "Feature"
    response["geometry"] = {"type": "Point",
                            "coordinates": [lon, lat, elevation]}
    response["when"] = {"interval": [start + offset,
                                     end + offset]
                        }          
    properties = {}
    properties["body"] = body
    
    rising_time = rising[0] + offset if rising[0] is not None else None
    az = arc_to_deg(setting[1]) if setting[1] is not None else None
    properties[f"{body.lower()}rise"] = {"time": rising_time,
                                 "azimuth": az
                                 }
    
    setting_time = setting[0] + offset if setting[0] is not None else None
    az = arc_to_deg(setting[1]) if setting[1] is not None else None
    properties[f"{body.lower()}set"] = {"time": setting_time,
                                "azimuth": az
                                }
    events = [None,None]
    if body == "Sun":
        events = ["Solarnoon", "solarmidnight"]
    elif body == "Moon":
        events = ["high_moon", "low_moon"]
    
    properties[events[0]] = {
                             "time": meridian[0] + offset,
                             "altitude": arc_to_deg(meridian[1]),
                             "distance": round(float(meridian[2]), 2),
                             "visible": str(meridian[3])
                             }
                             
    properties[events[1]] = {
                             "time": antimeridian[0] + offset,
                             "altitude": arc_to_deg(antimeridian[1]),
                             "distance": round(float(antimeridian[2]), 2),
                             "visible": str(antimeridian[3])
                             }
    if moonphase:
        properties["moonphase"] = {"value": round(moonphase.degrees, 2)}
    response["properties"] = properties
    return (response)

def arc_to_deg(input) -> float:
    """
    converts input string on the format
    \"xx deg xx' xx"\" to float. I.e converts
    arcminutes and arcsedonds to float.
    """

    float_vals = re.findall(r"\d+(?:\.\d+)?", input)
    float_vals = (float(float_vals[0])
                 + float(float_vals[1]) / 60
                 + float(float_vals[2]) / 3600)
    if input[0] == "-":
        float_vals = -float_vals
    return(round(float_vals, 3))