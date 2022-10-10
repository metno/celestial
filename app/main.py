#!/usr/bin/env python3

import uvicorn
import logging
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from routes.sunrise import router
from exception_handler import http_exception_handler


#################################
# Setting up logging module     #
#################################
import logging
logger = logging.getLogger()
logging.basicConfig(level=logging.INFO,
                    filemode="a",
                    datefmt='%Y-%m-%d %H:%M:%S',
                    format=" [%(levelname)s] (%(asctime)s) %(message)s",
                    )


app = FastAPI(docs_url="/v3/docs")
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
           "Description: Application for requesting rising and setting of The Sun and Moon.")

app.add_exception_handler(HTTPException,
                          http_exception_handler)


if __name__ == "__main__":

    uvicorn.run("main:app",
                host='0.0.0.0',
                port=5000,
                reload=True)

