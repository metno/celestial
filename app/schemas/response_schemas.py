from pydantic import BaseModel
from typing import List, Optional, Union

class geometry(BaseModel):
    type: str
    coordinates: List[Union[float, float, int]] = [0.0, 0.0, 0]

class when(BaseModel):
    interval: List[str]

class rise_set(BaseModel):
    time: str
    azimuth: float

class noon(BaseModel):
    time: str
    altitude: float
    #distance: float
    visible: bool

class properties(BaseModel):
    body: str
    rise: rise_set
    set: rise_set
    meridian_crossing: noon
    antimeridian_crossing: noon

class phase(BaseModel):
    value: float

class events(BaseModel):
    copyright: str
    licenseURL: str
    type: str
    geometry: geometry
    when: when
    properties: properties
    moonphase: Optional[phase]