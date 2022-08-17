#!/usr/bin/env python3

import uvicorn
import ephem
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from routes.sunrise import router
from typing import Optional
app = FastAPI()
app.include_router(router)
origins = [
    "https://api.met.no/",
]

app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )

@app.get("/healthz",
         response_class=HTMLResponse)
def healthz():
    return("System: Sunrise<br/>"
       "Service: Sunrise<br/>"
       "Version: dev<br/>"
       "Responsible: haakont<br/>"
       "Depends: api.met.no<br/>"
       "Status: Ok<br/>"
       "Description: Tool for meteorologists to store "
       "and create weather alert warnings")



def banan():

    date = '2018/9/20'

    sun = ephem.Sun()
    sun.compute(date)
    fred = ephem.Observer()
    fred.lon  = str(-66.666667) #Note that lon should be in string format
    fred.lat  = str(45.95)      #Note that lat should be in string format

    #Elevation of Fredericton, Canada, in metres
    fred.elev = 20

    #To get U.S. Naval Astronomical Almanac values, use these settings
    fred.pressure= 0
    fred.horizon = '-0:34'

    sunrise=fred.previous_rising(sun) #Sunrise
    print('Sun in', list(ephem.constellation(sun))[1], sunrise)
    return("a")


if __name__ == "__main__":

    uvicorn.run("main:app",
                host='0.0.0.0',
                port=5000,
                reload=True)

