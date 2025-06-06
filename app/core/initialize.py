import logging
import colorlog
import os
from skyfield import api


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


def configure_logging():
    """
    Configures the logging for the application.
    The log level can be set via the LOG_LEVEL environment variable.
    If not set, it defaults to INFO."""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_colors = {
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'bold_red',
    }

    formatter = colorlog.ColoredFormatter(
        "%(asctime)s - %(name)s - %(log_color)s%(levelname)s%(reset)s - %(message)s",
        log_colors=log_colors,
        reset=True,
        style='%',
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    # Create a named logger for the application
    logger = logging.getLogger("celestial")
    # Clear existing handlers to avoid duplicate logs
    if logger.hasHandlers():
        logger.handlers.clear()
    logger.setLevel(getattr(logging, log_level, logging.INFO)) 
    logger.addHandler(handler)
    logger.propagate = False
    
    return(logger)