

def make_response(setting, rising, meridian, antimeridian,
                  start, end, body, lat, lon, elevation, moonphase, offset):
    response = {}
    response["type"] = "Feature"
    response["geometry"] = {"type": "Point",
                            "coordinates": [lon, lat, elevation]}
    response["when"] = {"interval": [start + offset,
                                     end + offset]
                        }
                        
    properties = {}
    properties["body"] = body
    properties[f"{body}rise"] = {"time": rising[0],
                                 "azimuth": rising[1],
                                 "distance": rising[2]}
    properties[f"{body}set"] = {"time": setting[0],
                                "azimuth": setting[1],
                                "distance": setting[2]}
    
    events = [None,None]
    if body == "Sun":
        events = ["Solarnoon", "solarmidnight"]
    elif body == "Moon":
        events = ["high_moon", "low_moon"]
    
    properties[events[0]] = {
                             "time": meridian[0],
                             "altitude": meridian[1]
                             }
                             
    properties[events[1]] = {
                             "time": antimeridian[0],
                             "altitude": antimeridian[1]
                             }
    if moonphase:
        properties["moonphase"] = {"value": moonphase.degrees}
    response["properties"] = properties
    return (response)    