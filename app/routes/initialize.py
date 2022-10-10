from skyfield import api
from fastapi import APIRouter

router = APIRouter()

class Initialize():
    """
    Pre-load ephemeris table once.
    """
    def __init__(self):
        self.eph = api.load('de440s.bsp')

@router.on_event("startup")
def init_eph():
    return(Initialize().eph)