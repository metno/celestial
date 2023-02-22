
def make_response(setting, rising, meridian, antimeridian,
                  start, end, body, lat, lon,
                  moonphase, offset) -> dict:
    response = {}
    response["copyright"] = "MET Norway"
    response["licenseURL"] = "https://api.met.no/license_data.html"

    response["type"] = "Feature"
    response["geometry"] = {"type": "Point",
                            "coordinates": [lon, lat]} # removed altitude

    response["when"] = {"interval": [start + ":00Z",
                                     end + ":00Z"]
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

    if meridian[0] is not None:
        properties[events[0]] = {
                                 "time": meridian[0] + offset,
                                 "disc_centre_elevation": round(meridian[1], 2),
                                 "visible": str(meridian[2]) == "True"
                                 }
    else:
        properties[events[0]] = {
                                 "time": None,
                                 "disc_centre_elevation": None,
                                 "visible": None
                                 }
    if antimeridian[0] is not None:
        properties[events[1]] = {
                                 "time": antimeridian[0] + offset,
                                 "disc_centre_elevation": round(antimeridian[1], 2),
                                 "visible": str(antimeridian[2]) == "True"
                                 }
    else:
        properties[events[1]] = {
                                 "time": None,
                                 "disc_centre_elevation": None,
                                 "visible": None
                                 }
    if moonphase:
        properties["moonphase"] = round(moonphase.degrees, 2)
    response["properties"] = properties
    return (response)
