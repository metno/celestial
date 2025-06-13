from pydantic import BaseModel
from typing import List, Optional, Literal

class Geometry(BaseModel):
    type: Literal["Point"] = "Point"
    coordinates: list[float]  # [longitude, latitude] without altitude

class When(BaseModel):
    interval: List[str]

class RisingEvent(BaseModel):
    time: str | None
    azimuth: float | None

class MeridianCrossingEvent(BaseModel):
    time: str | None
    disc_centre_elevation: float | None
    visible: bool | None

class SunProperties(BaseModel):
    body: Literal["Sun"] = "Sun"
    sunrise: RisingEvent
    sunset: RisingEvent
    solarnoon: MeridianCrossingEvent
    solarmidnight: MeridianCrossingEvent

class MoonProperties(BaseModel):
    body: Literal["Moon"] = "Moon"
    moonrise: RisingEvent
    moonset: RisingEvent
    high_moon: MeridianCrossingEvent
    low_moon: MeridianCrossingEvent
    moonphase: float

class ResponseModel(BaseModel):
    copyright: Literal["MET Norway"] = "MET Norway" 
    licenseURL: Literal["https://api.met.no/license_data.html"] = "https://api.met.no/license_data.html"
    type: Literal["Feature"] = "Feature"
    geometry: Geometry
    when: When
    properties: SunProperties | MoonProperties


def make_response(setting, rising, meridian, antimeridian,
                  start, end, body, lat, lon,
                  moonphase, offset) -> ResponseModel:
    """
    Construct a response model for celestial event data.

    Args:
        setting: Tuple containing (time, azimuth) for the setting event.
        rising: Tuple containing (time, azimuth) for the rising event.
        meridian: Tuple containing (time, disc_centre_elevation, visible) for the meridian crossing event.
        antimeridian: Tuple containing (time, disc_centre_elevation, visible) for the antimeridian crossing event.
        start: Start time string (ISO format, without ":00Z" suffix).
        end: End time string (ISO format, without ":00Z" suffix).
        body: String, either "Sun" or "Moon", indicating the celestial body.
        lat: Latitude as float.
        lon: Longitude as float.
        moonphase: Object with a 'degrees' attribute (float) for the moon phase, or None.
        offset: String to append to event times (e.g., timezone offset).

    Returns:
        dict: Dictionary representation of the response model for the specified celestial body and events.

    Raises:
        ValueError: If 'body' is not "Sun" or "Moon".
    """
    geometry = Geometry(coordinates=[lon, lat])
    when = When(interval=[start + ":00Z", end + ":00Z"])

    rising_time = rising[0] + offset if rising[0] is not None else None
    rising_az = round(rising[1], 2) if rising[1] is not None else None
    setting_time = setting[0] + offset if setting[0] is not None else None
    setting_az = round(setting[1], 2) if setting[1] is not None else None

    if body == "Sun":
        properties = SunProperties(
            sunrise=RisingEvent(time=rising_time, azimuth=rising_az),
            sunset=RisingEvent(time=setting_time, azimuth=setting_az),
            solarnoon=MeridianCrossingEvent(
                time=meridian[0] + offset if meridian[0] is not None else None,
                disc_centre_elevation=round(meridian[1], 2) if meridian[1] is not None else None,
                visible=str(meridian[2]) == "True" if meridian[2] is not None else None
            ),
            solarmidnight=MeridianCrossingEvent(
                time=antimeridian[0] + offset if antimeridian[0] is not None else None,
                disc_centre_elevation=round(antimeridian[1], 2) if antimeridian[1] is not None else None,
                visible=str(antimeridian[2]) == "True" if antimeridian[2] is not None else None
            )
        )
    elif body == "Moon":
        properties = MoonProperties(
            moonrise=RisingEvent(time=rising_time, azimuth=rising_az),
            moonset=RisingEvent(time=setting_time, azimuth=setting_az),
            high_moon=MeridianCrossingEvent(
                time=meridian[0] + offset if meridian[0] is not None else None,
                disc_centre_elevation=round(meridian[1], 2) if meridian[1] is not None else None,
                visible=str(meridian[2]) == "True" if meridian[2] is not None else None
            ),
            low_moon=MeridianCrossingEvent(
                time=antimeridian[0] + offset if antimeridian[0] is not None else None,
                disc_centre_elevation=round(antimeridian[1], 2) if antimeridian[1] is not None else None,
                visible=str(antimeridian[2]) == "True" if antimeridian[2] is not None else None
            ),
            moonphase=round(moonphase.degrees, 2) if moonphase else None
        )
    else:
        raise ValueError("body must be 'Sun' or 'Moon'")

    return ResponseModel(
        geometry=geometry,
        when=when,
        properties=properties).model_dump()
