#!/usr/bin/env python3

#import uvicorn
import logging
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
from routes.sunrise import router
from exception_handler import http_exception_handler
from time import perf_counter
from anyio.lowlevel import RunVar
from anyio import CapacityLimiter
#################################
# Setting up logging module     #
#################################
import logging

app = FastAPI(openapi_url="/openapi.json",
              docs_url="/docs")

#RunVar("_default_thread_limiter").set(CapacityLimiter(4))

app.include_router(router)
origins = [
    "https://api.met.no/"]

app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"])

#logger = logging.getLogger("uvicorn.access")

#@app.on_event("startup")
#async def startup_event():
#    console_formatter = uvicorn.logging.ColourizedFormatter(
#        "{levelprefix} ({asctime}) : {message}","%Y-%m-%d %H:%M:%S",
#        style="{", use_colors=True,
#        )
#    logger.handlers[0].setFormatter(console_formatter)
#    RunVar("_default_thread_limiter").set(CapacityLimiter(2))

#@app.middleware("http")
#async def add_process_time_header(request: Request,
#                                  call_next):
#    start_time = perf_counter()
#    response = await call_next(request)
#    process_time = perf_counter() - start_time
#    logger.info(f"response-time: {round(process_time, 4)}s")
#    return(response)

#@app.get("/healthz",
#         response_class=HTMLResponse)
#def healthz():
#    return("System: Sunrise<br/>"
#           "Service: Sunrise<br/>"
#           "Version: dev<br/>"
#           "Responsible: haakont, mateuszmr<br/>"
#           "Depends: api.met.no<br/>"
#           "Status: Ok<br/>"
#           "Description: Application for requesting rising and setting of The Sun and Moon.")

#app.add_exception_handler(HTTPException,
#                          http_exception_handler)


#if __name__ == "__main__":
#
#    uvicorn.run("main:app",
#                host='0.0.0.0',
#                port=8080,
#                workers=4,
#                limit_concurrency=20)

