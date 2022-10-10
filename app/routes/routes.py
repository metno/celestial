from fastapi import APIRouter

##############
# App routes #
##############

from routes import sunrise, initialize

routes = APIRouter()
routes.include_router(sunrise.router)
routes.include_router(initialize.router)