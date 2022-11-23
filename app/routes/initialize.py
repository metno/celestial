from skyfield import api
from fastapi import APIRouter

router = APIRouter()
eph = None

class Initialize():
    """
    Pre-load ephemeris table once.
    """
    def __init__(self):
        self.eph = api.load('de440s.bsp')


#@router.on_event("startup")
def init_eph():
    global eph
    if(eph == None):
      eph = Initialize().eph
    return eph
