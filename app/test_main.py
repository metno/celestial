from fastapi import FastAPI
from fastapi.testclient import TestClient
from main import app
from http import HTTPStatus
import datetime

client = TestClient(app)

def test_known_date():
    """
    This simple request should never fail
    """
    response = client.get("/?date=2022-08-22&lat=51.477&lon=-0.001&elevation=0")
    assert response.status_code == HTTPStatus.OK

def test_north_pole():
    """
    Only one sunset and sunrise per year on the north pole.
    """
    start_date = datetime.date(2022, 1, 1)
    end_date = datetime.date(2022, 12, 31)
    delta = datetime.timedelta(days=1)

    n_sunrise = 0
    n_sunset = 0
    while start_date <= end_date:
        start_date += delta
        date = start_date.strftime("%Y-%m-%d")
        response = client.get(f"/?date={date}&lat=89.9&lon=20&elevation=0")
        response = response.json()
        sunset = response["time"][0]["sunset"]["time"]
        sunrise = response["time"][0]["sunrise"]["time"]
        if sunset is not None:
            n_sunset += 1
        if sunrise is not None:
            n_sunrise +=1
    assert n_sunrise == 1
    assert n_sunset == 1 
        
