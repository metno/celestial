#!/usr/bin/env python3

import uvicorn
import logging
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
from routes.sunrise import router
from starlette_prometheus import metrics, PrometheusMiddleware
from exception_handler import (http_exception_handler,
                              unexpected_exception_handler)
from time import perf_counter
#################################
# Setting up logging module     #
#################################
import logging

app = FastAPI(openapi_url="/openapi.json",
              docs_url="/docs")


app.include_router(router)
origins = [
    "https://api.met.no/"]

app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"])

app.add_middleware(PrometheusMiddleware)
app.add_route("/metrics/", metrics)
logger = logging.getLogger("uvicorn.access")

@app.on_event("startup")
async def startup_event():
    """
    Set logging format
    """
    console_formatter = uvicorn.logging.ColourizedFormatter(
        "{levelprefix} ({asctime}) : {message}","%Y-%m-%d %H:%M:%S",
        style="{", use_colors=True,
        )
    logger.handlers[0].setFormatter(console_formatter)

@app.middleware("http")
async def add_process_time_header(request: Request,
                                  call_next):
    start_time = perf_counter()
    response = await call_next(request)
    process_time = perf_counter() - start_time
    logger.info(f"response-time: {round(process_time, 4)}s")
    return(response)

@app.get("/healthz",
         response_class=HTMLResponse)
def healthz():
    return("System: Sunrise<br/>"
           "Service: Sunrise<br/>"
           "Version: dev<br/>"
           "Responsible: haakont, mateuszmr<br/>"
           "Depends: k8s.met.no<br/>"
           "Status: Ok<br/>"
           "Description: Application for requesting rising and setting of The Sun and Moon.")

@app.get("/")
def home() -> str:
    return ("This is the Celestial backend for calculating rising and setting of the Sun and Moon! "
            "Please refer to the /docs endpoint for an OpenAPI spec documenting how to query the API.")

app.add_exception_handler(HTTPException,
                          http_exception_handler)
app.add_exception_handler(Exception,
                          unexpected_exception_handler)

if __name__ == "__main__":

    uvicorn.run("main:app",
                host='0.0.0.0',
                port=5000,
                workers=4,
                reload=True,
                limit_concurrency=20)

