#!/usr/bin/env python3
import uvicorn
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

if __name__ == "__main__":

    uvicorn.run("main:app",
                host='0.0.0.0',
                port=5000,
                reload=True)

