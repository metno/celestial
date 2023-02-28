"""
One-time quality control of celestial calculations against AA USNO,
version 2 and 2.1 of weatherapi.
"""

import datetime
from dateutil import parser
import unittest
import requests
import os
import json
import random
from timezonefinder import TimezoneFinder
import pytz
import numpy
import time
import colorama
from colorama import Fore, Back, Style
colorama.init()

verbose = True

class CelestialQA(unittest.TestCase):

    def fetch_usno(self, coords: tuple, selected_time: datetime, skip_cache = False, body = "sun") -> tuple[float, float, datetime.datetime, datetime.datetime]:
        """
        Fetch data from AA USNO. If we have an offline datafile, return that, if not fetch from API.

        We use an ID to present ourself.
        See https://aa.usno.navy.mil/data/api for docs.
        """
        usno_jsondata = None
        datapath = "app/testdata/"
        os.makedirs(datapath, exist_ok=True)
        usno_datafile = f"{datapath}usno_{coords[0]}_{coords[1]}_{selected_time.strftime('%Y-%m-%d')}.json"

        base_url = 'https://aa.usno.navy.mil/api/rstt/oneday?ID=larsfp@met.no'
        url = base_url + \
            '&date=' + \
            selected_time.strftime('%Y-%m-%d') + \
            f'&tz={self.get_coords_offset_minimal(coords, selected_time)}' + \
            '&coords=' + \
            str(coords[0]) + ',' + str(coords[1]) + \
            "&body=" + body
        if verbose:
            print(f"fetch_usno <{url}>")

        if not skip_cache and os.path.isfile(usno_datafile):
            if verbose:
                print(Fore.GREEN + "Using cached data for USNO" + Fore.RESET)
            with open (usno_datafile, mode='r', encoding='utf-8') as f:
                usno_jsondata = json.load(f)
        else:
            usno_response = requests.get(url, timeout=10)
            usno_jsondata = usno_response.json()
            if not skip_cache:
                with open(usno_datafile, mode='w', encoding='utf-8') as f:
                    f.write(json.dumps(usno_jsondata, indent=4))

        lat = usno_jsondata['geometry']['coordinates'][1]
        lon = usno_jsondata['geometry']['coordinates'][0]

        offset = self.get_coords_offset(coords, selected_time)
        rise = None
        rise_date = f"{usno_jsondata['properties']['data']['year']}-{usno_jsondata['properties']['data']['month']}-{usno_jsondata['properties']['data']['day']}"
        for field in usno_jsondata['properties']['data'][body + 'data']:
            if str(field['phen']).lower() == "rise":
                rise = parser.parse(f"{rise_date} {field['time']} {offset}")

        set = None
        for field in usno_jsondata['properties']['data'][body + 'data']:
            if str(field['phen']).lower() == "set":
                set = parser.parse(f"{rise_date} {field['time']} {offset}")

        return lat, lon, rise, set

    def fetch_celestial(self, coords: tuple, selected_time: datetime, body = "sun", base_url = None) -> tuple[float, float, datetime.datetime, datetime.datetime]:
        """
        Fetch data from celestial.
        """

        if not base_url:
            base_url = 'https://celestial.k8s.met.no'
        url = f"{base_url}/events/{body}?elevation=0&date=" + \
                            selected_time.strftime('%Y-%m-%d') + \
                            f"&offset={self.get_coords_offset(coords, selected_time)}" + \
                            "&lat=" + \
                            str(coords[0]) + "&lon=" + str(coords[1])
        if verbose:
            print("fetch_celestial", url)
        response = requests.get(url, timeout=10, headers={'User-Agent': 'larsfp@met.no'})
        response_json = response.json()

        lat = response_json['geometry']['coordinates'][1]
        lon = response_json['geometry']['coordinates'][0]

        rise = set = None
        try:
            rise = self.parse_celestial_datetime(response_json["properties"][body + "rise"]["time"])
        except TypeError: # No rise
            pass
        try:
            set = self.parse_celestial_datetime(response_json["properties"][body + "set"]["time"])
        except TypeError: # No set
            pass

        return lat, lon, rise, set

    def fetch_weatherapi21(self, coords: tuple, selected_time: datetime, body = "sun", base_url = "https://api.met.no/weatherapi/sunrise/2.1/.json") -> tuple[float, float, datetime.datetime, datetime.datetime]:
        """
        Fetch data from https://api.met.no/weatherapi/sunrise/2.1/documentation
        """

        url = base_url + "?date=" + \
            selected_time.strftime('%Y-%m-%d') + \
            f"&offset={self.get_coords_offset(coords, selected_time)}" + \
            "&lat=" + \
            str(coords[0]) + "&lon=" + str(coords[1])
        if verbose:
            print("fetch_weatherapi21", url)
        response = requests.get(url, timeout=10, headers={'User-Agent': 'larsfp@met.no'})
        response_json = response.json()
        lat = response_json['location']['latitude']
        lon = response_json['location']['longitude']

        rise = set = None
        try:
            rise = parser.parse(response_json["location"]["time"][0][body + "rise"]["time"])
        except KeyError: # No sunrise
            pass
        try:
            set = parser.parse(response_json["location"]["time"][0][body + "set"]["time"])
        except KeyError: # No sunset
            pass

        return lat, lon, rise, set

    def fetch_weatherapi20(self, coords: tuple, selected_time: datetime, body = "sun")-> tuple[float, float, datetime.datetime, datetime.datetime]:
        """
        Fetch data from https://api.met.no/weatherapi/sunrise/2.0/documentation
        """
        return self.fetch_weatherapi21(coords=coords, selected_time=selected_time, body=body, base_url="https://api.met.no/weatherapi/sunrise/2.0/.json")

    def compare_APIs(self, coords: tuple, selected_time_utc = None, body = "sun", celestial_base_url = None):
        """
        Fetch data from APIs and compare results.
        """
        if not selected_time_utc:
            selected_time_utc = datetime.datetime.strptime("2010-12-24 12:00", "%Y-%m-%d %H:%M")
            selected_time_utc = selected_time_utc.replace(tzinfo=pytz.UTC)

        # Celestial
        c_lat, c_lon, c_sunrise, c_sunset = self.fetch_celestial(coords, selected_time_utc, body=body, base_url=celestial_base_url)

        # WeatherAPI 2.1
        wapi21_lat, wapi21_lon, wapi21_sunrise, wapi21_sunset = self.fetch_weatherapi21(coords, selected_time_utc, body=body)

        # WeatherAPI 2.0
        wapi20_lat, wapi20_lon, wapi20_sunrise, wapi20_sunset = self.fetch_weatherapi20(coords, selected_time_utc, body=body)

        # USNO
        usno_lat, usno_lon, us_sunrise, us_sunset = self.fetch_usno(coords, selected_time_utc, body=body)

        # Compare coordinates
        self.assertTupleEqual(coords, (usno_lat, usno_lon))
        self.assertTupleEqual(coords, (c_lat, c_lon))
        # self.assertTupleEqual(coords, (wapi21_lat,wapi21_lon))
        # if verbose:
        #     print("\nAsked for coords", coords)
        #     print(" * Celestial     ", c_lat, c_lon)
        #     print(" * USNO          ", usno_lat, usno_lon)
        #     print(" * WAPI2.1       ", wapi21_lat, wapi21_lon)
        #     print(" * WAPI3.0       ", wapi30_lat, wapi30_lon, "\n")

        # Compare sunrise
        if c_sunrise:
            print(f"Celestial {body}rise {c_sunrise.strftime('%Y-%m-%d %H:%M %z')}")
        if us_sunrise:
            print(f" * USNO           {us_sunrise.strftime('%Y-%m-%d %H:%M %z')}, diff {self.format_diff(c_sunrise, us_sunrise, ignore_date=True, colors=True)}s")
        if wapi21_sunrise:
            print(f" * wapi2.1        {wapi21_sunrise.strftime('%Y-%m-%d %H:%M %z')}, diff {self.format_diff(c_sunrise, wapi21_sunrise)}s")
        if wapi20_sunrise:
            print(f" * wapi2.0        {wapi20_sunrise.strftime('%Y-%m-%d %H:%M %z')}, diff {self.format_diff(c_sunrise, wapi20_sunrise)}s", "\n")

        # Compare sunset
        if c_sunset:
            print(f"Celestial {body}set  {c_sunset.strftime('%Y-%m-%d %H:%M %z')}")
        if us_sunset:
            print(f" * USNO           {us_sunset.strftime('%Y-%m-%d %H:%M %z')}, diff {self.format_diff(c_sunset, us_sunset, colors=True)}s")
        if wapi21_sunset:
            print(f" * wapi2.1        {wapi21_sunset.strftime('%Y-%m-%d %H:%M %z')}, diff {self.format_diff(c_sunset, wapi21_sunset)}s")
        if wapi20_sunset:
            print(f" * wapi3.0        {wapi20_sunset.strftime('%Y-%m-%d %H:%M %z')}, diff {self.format_diff(c_sunset, wapi20_sunset)}s\n")

        # dateandtime
        print(f"Timeanddate.com for this location: <https://www.timeanddate.com/sun/@{coords[0]}%2C{coords[1]}?month={selected_time_utc.strftime('%m')}&year={selected_time_utc.strftime('%Y')}>")
        # location
        print(f"Map <https://www.openstreetmap.org/search?whereami=1&query={coords[0]}%2C{coords[1]}#map=9/{coords[0]}/{coords[1]}> \n")

        # Return data for statistics
        return c_sunrise, c_sunset, us_sunrise, us_sunset, wapi20_sunrise, wapi20_sunset, wapi21_sunrise, wapi21_sunset

    def format_diff(self, first, second, ignore_date=False, colors=False):
        maxdiff = 120

        if not first or not second:
            return 'NaN'

        diff = self.calculate_diff(first, second, ignore_date)
        result = diff

        if abs(diff) > maxdiff:
            result = (Fore.RED if colors else '') + str(diff) + Fore.RESET
        elif abs(diff) > maxdiff/2:
            result = (Fore.YELLOW if colors else '') + str(diff) + Fore.RESET
        return result

    def calculate_diff(self, first, second, ignore_date=False):
        """ US NO gives sunset happening on the given date,
            while celestial gives sunset matching sunrise.
            Thus we fudge the data to make it match.
        """
        diff = (first-second).total_seconds()

        if ignore_date:
            if diff > 43200:
                print("Warning, time fudged to match date")
                diff -= 86400
        return diff

    def generate_random_coords(self, count = 10) -> list:
        """
        Generate <count> amount of random coordinates on earth in format lat, lon
        """
        locations = []

        for i in range (0, count):
            lat=(random.randint(-9000,9000))/100
            lon=(random.randint(-18000,18000))/100
            locations.append((lat, lon))
            if verbose:
                print(f"({lat}, {lon}),")
        return locations

    def generate_random_timestamps(self, count = 1) -> datetime:
        """
        Generate <count> amount of random timestamps
        """
        timestamps = []
        i = 0

        while i < count:
            newtime = None
            try:
                newtime = datetime.datetime.strptime("%s-%s-%s %s:%s" % (
                    random.randint(1990, 2025), # year
                    random.randint(1, 12),      # month
                    random.randint(1, 31),      # day
                    random.randint(0, 23),      # hour
                    random.randint(0, 59),      # minute
                ), "%Y-%m-%d %H:%M")
            except ValueError: # When days 29-31 don't exist
                continue

            if verbose:
                print("Generated random timestamp", newtime)
            timestamps.append(newtime)
            i+=1

        return timestamps

    def compare_random(self, count = 0, delay = 0.5, selected_time = None, coords_list = None, body = "sun", celestial_base_url = None):
        """
        Generate (or be supplied with) lots of random coordinates. Fetch data for each and compare sunrise diffs. Do some basic calculations on result.
        """
        dataset_usno = []
        dataset_wapi21 = []
        dataset_wapi20 = []
        if not selected_time:
            selected_time = datetime.datetime(2010, 12, 24)

        if not coords_list:
            coords_list = []
            coords_list.append(self.generate_random_coords(count))

        for coords in coords_list:
            if verbose:
                print("Testing coords", coords)
            c_sunrise, c_sunset, us_sunrise, us_sunset, wapi20_sunrise, \
                wapi20_sunset, wapi21_sunrise, wapi21_sunset = \
                self.compare_APIs(coords=coords, selected_time_utc=selected_time, body=body)

            if us_sunrise:
                dataset_usno.append(abs(self.calculate_diff(c_sunrise, us_sunrise, ignore_date=True)))
                dataset_wapi21.append(abs(self.calculate_diff(c_sunrise, wapi21_sunrise, ignore_date=True)))
                dataset_wapi20.append(abs(self.calculate_diff(c_sunrise, wapi20_sunrise, ignore_date=True)))
            if us_sunset:
                dataset_usno.append(abs(self.calculate_diff(c_sunset, us_sunset, ignore_date=True)))
                dataset_wapi21.append(abs(self.calculate_diff(c_sunset, wapi21_sunset, ignore_date=True)))
                dataset_wapi20.append(abs(self.calculate_diff(c_sunset, wapi20_sunset, ignore_date=True)))

            if len(dataset_usno)> 0:
                print('Count:', len(dataset_usno)/2)
                print(f'Mean USNO: {round(numpy.mean(dataset_usno))} s')
                print(f'Standard Deviation USNO: {round(numpy.std(dataset_usno))} s')
                print(f'Mean wapi20: {round(numpy.mean(dataset_wapi20))} s')
                print(f'Standard Deviation wapi20: {round(numpy.std(dataset_wapi20))} s')
                print(f'Mean wapi21: {round(numpy.mean(dataset_wapi21))} s')
                print(f'Standard Deviation wapi21: {round(numpy.std(dataset_wapi21))} s')

            print(dataset_usno)
            # print(dataset_wapi20)
            # print(dataset_wapi21)

            time.sleep(delay)

    def get_coords_localtime(self, coords: tuple, selected_time_utc: datetime) -> datetime:
        """
        Return local time for a location and UTC timestamp
        """
        local_timezone = TimezoneFinder().timezone_at(lat=coords[0], lng=coords[1]) # returns 'Europe/Berlin'
        tz = pytz.timezone(local_timezone)
        #local_time = tz.localize(selected_time_utc)
        local_time = selected_time_utc.astimezone(tz)
        # if verbose:
        #     print("Found time zone", local_timezone, f"converting {selected_time_utc.strftime('%Y-%m-%d %H:%M %Z')} to {local_time.strftime('%Y-%m-%d %H:%M %Z')}.")
        return local_time

    def get_coords_offset(self, coords: tuple, selected_time_utc: datetime) -> str:
        """
        Return timezone offset for a location. Needs a time as offset will change during the year.
        """
        local_timezone = TimezoneFinder().timezone_at(lat=coords[0], lng=coords[1]) # returns 'Europe/Berlin'
        tz = pytz.timezone(local_timezone)
        offset = pytz.timezone(local_timezone).localize(selected_time_utc.replace(tzinfo=None)).strftime('%z')
        if len(offset) > 0:
            offset = offset[0:-2] + ":" + offset[-2:]
        return offset

    def get_coords_offset_minimal(self, coords: tuple, selected_time_utc: datetime) -> str:
        """
        US NO wants 4, 4.5, -7, -7.25. Pytz gives +0400, +0430, -0700, -0715
        """
        local_timezone = TimezoneFinder().timezone_at(lat=coords[0], lng=coords[1]) # returns 'Europe/Berlin'
        tz = pytz.timezone(local_timezone)
        offset = pytz.timezone(local_timezone).localize(selected_time_utc.replace(tzinfo=None)).strftime('%z')
        if len(offset) > 0:
            hour = str(round(int(offset[0:-2]), 0)) # Convert hour part
            minutes = int(offset[-2:])
            if minutes != 0:                          # Convert minute part if not zero
                return hour + "." + str(int(offset[-2:])/60).split('.')[1]
        return hour

    def get_coords_timezone(self, coords: tuple, selected_time_utc: datetime) -> str:
        """
        Return timezone shorthand for a location.
        """
        local_timezone = TimezoneFinder().timezone_at(lat=coords[0], lng=coords[1]) # returns 'Europe/Berlin'
        tz = pytz.timezone(local_timezone)
        shorthand = pytz.timezone(local_timezone).localize(selected_time_utc.replace(tzinfo=None)).strftime('%Z')
        return shorthand

    def parse_celestial_datetime(self, timestamp: str):
        """
        Celestial has an unstandard way of formating offset. Parse and fix.
        """
        # Offset comes as:
        # 0530 13:00 change to 0530 +1300
        # 0530-05:00 change to 0530 -0500
        date = timestamp
        offset = ''
        if ' ' in timestamp:
            date, offset = timestamp.split(' ')
            offset = "+" + offset.replace(':', '')
        elif '-' in timestamp:
            date, offset = timestamp[0:-6], timestamp[-6:]
            offset = offset.replace(':', '')

        return datetime.datetime.strptime(date + " " + offset, "%Y-%m-%dT%H:%M %z")


if __name__ == '__main__':
    pass
    # CelestialQA().generate_random_timestamps(1)
    # CelestialQA().generate_random_coords(1)

    # Met.no Oslo, default time 2010-12-24
    # CelestialQA().compare_APIs(coords=(59.94, 10.71), celestial_base_url='http://0.0.0.0:5000')
    CelestialQA().compare_APIs(coords=(59.94, 10.71))

    # print("New york statue of liberty, 2010-12-24")
    # CelestialQA().compare_APIs(coords=(40.689,-74.044))

    # print("auckland sky cafe, 2010-12-24")
    # CelestialQA().compare_APIs(coords=(-36.84846,174.76219))

    # Find a random location and random time and compare APIs
    # CelestialQA().compare_random(1)
