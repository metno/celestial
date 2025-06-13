#!/usr/bin/env python3

import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from routes.sunrise import router
from exception_handler import (http_exception_handler,
                              unexpected_exception_handler)
from time import perf_counter
from core.initialize import configure_logging


logger = configure_logging()
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


@app.middleware("http")
async def add_process_time_header(request: Request,
                                  call_next):
    start_time = perf_counter()
    response = await call_next(request)
    process_time = perf_counter() - start_time
    logger.info(f"Request: {request.method} {request.url} with status code {response.status_code} completed in {process_time:.4f} seconds")
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


#  Remove comments on these lines if you want to run the application directly
#  without building and running a docker image.

#if __name__ == "__main__":
#
#    uvicorn.run("main:app",
#                host='0.0.0.0',
#                port=5000,
#                workers=4,
#                reload=True,
#                access_log=False,
#                limit_concurrency=20)

