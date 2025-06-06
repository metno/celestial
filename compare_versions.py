"""
compare_versions.py

Usage:
    python compare_versions.py <API_URL_1> <API_URL_2>

Example:
    python3 compare_versions.py http://localhost:8080 https://celestial-dev.k8s.met.no

This script compares the JSON responses from two API endpoints for randomly generated dates and coordinates.
"""

import httpx
import numpy as np
import difflib
import json
import sys
from urllib.parse import urljoin


N = 50

def main():

    if len(sys.argv) < 2:
        raise Exception("Please provide two API URLs as arguments.")
    api1 = str(sys.argv[1])
    api2 = str(sys.argv[2])

    print(f"Comparing {api1} and {api2} ...")
    lat = np.random.uniform(-90, 90, N)
    lon = np.random.uniform(-180, 180, N)

    day = np.random.randint(1,27, N) # 27 to avoid querying february out of range
    month = np.random.randint(1,12, N)
    year = np.random.randint(1990, 2025, N)

    for i in range(N):
        query_string = f"/events/sun?date={year[i]}-{str(month[i]).zfill(2)}-{str(day[i]).zfill(2)}&lat={lat[i]}&lon={lon[i]}&offset=%2B00%3A00"
        r1 = httpx.get(urljoin(api1, query_string))
        r2 = httpx.get(urljoin(api2, query_string))
        str1 = json.dumps(r1.json(), indent=2, sort_keys=True)
        str2 = json.dumps(r2.json(), indent=2, sort_keys=True)

        diff = difflib.unified_diff(str1.splitlines(), str2.splitlines())
        
        try:
            assert r1.json() == r2.json()
            print(f"Responses from {api1} and {api2} for query string {query_string} are equal")
        except AssertionError:
            print(f"Responses from {api1} and {api2} for query string {query_string} are NOT equal. see diff below:")
            print('\n'.join(diff))

if __name__ == "__main__":
    main()