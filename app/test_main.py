import datetime
from fastapi.testclient import TestClient
from main import app
from http import HTTPStatus
from dateutil import parser
import unittest
import requests
import os
import json

client = TestClient(app)

class TestStringMethods(unittest.TestCase):

    def test_known_date(self):
        """
        Sunrise in Oslo 2010-12-24 occured on 09:19 local time
        Sunset in Oslo 2010-12-24 occured on 15:13 local time
        source (https://www.timeanddate.com/sun/norway/oslo?month=12&year=2010)

        Check that the Sunrise application reproduses this plus minus a few minutes
        """
        response = client.get("/events/sun?offset=%2B01%3A00&date=2010-12-24&lat=59.91&lon=10.75&elevation=0")
        response_json = response.json()
        sunset = response_json["properties"]["sunset"]["time"]
        sunrise = response_json["properties"]["sunrise"]["time"]
        sunset = parser.parse(sunset, ignoretz = True)
        sunrise = parser.parse(sunrise, ignoretz = True)
        min_tol_sunset = datetime.datetime(2010, 12, 24, 15, 12, 0)
        max_tol_sunset = datetime.datetime(2010, 12, 24, 15, 14, 0)
        min_tol_sunrise = datetime.datetime(2010, 12, 24, 9, 18, 0)
        max_tol_sunrise = datetime.datetime(2010, 12, 24, 9, 20, 0)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(min_tol_sunset < sunset < max_tol_sunset)
        self.assertTrue(min_tol_sunrise < sunrise < max_tol_sunrise)

    def test_north_pole(self):
        """
        Only one sunset and sunrise per year on the north pole.
        """

        start_date = datetime.date(2022, 1, 1)
        end_date = datetime.date(2022, 12, 31)
        delta = datetime.timedelta(days=1)

        n_sunrise = 0
        n_sunset = 0
        # print("Checking days of sunrise on north pole in 2022", end='')
        while start_date <= end_date:
            start_date += delta
            date = start_date.strftime("%Y-%m-%d")
            response = client.get(f"/events/sun?date={date}&lat=89.99&lon=20&elevation=0")
            response = response.json()
            sunset = response["properties"]["sunset"]["time"]
            sunrise = response["properties"]["sunrise"]["time"]
            #print(date, sunset, sunrise)
            # print(".", end='')

            if sunset not in ["polar day","polar night", None]:
                n_sunset += 1
            if sunrise not in ["polar day", "polar night", None]:
                n_sunrise +=1
        # print("")
        self.assertEqual(n_sunrise, 1)
        self.assertEqual(n_sunset, 1)


if __name__ == '__main__':
    unittest.main()