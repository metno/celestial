from asyncio import create_task, get_event_loop, sleep, run, exceptions
import genericpath
import time
from queue import Queue
from aiohttp import ClientSession, TraceConfig, client_exceptions
import numpy as np
import configparser
import sys
import json
import random
import signal
from datetime import datetime, timedelta


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def printe(str):
    print(bcolors.FAIL + str + bcolors.ENDC)


def printw(str):
    print(bcolors.WARNING + str + bcolors.ENDC)


async def on_request_start(session, trace_config_ctx, params):
    trace_config_ctx.start = get_event_loop().time()


async def on_request_end(session, trace_config_ctx, params):
    elapsed, url, method, status_code = get_event_loop().time() - trace_config_ctx.start, str(params.url), params.method, params.response.status
    #print("{}".format(params.response))
    print("{}, {}, {}, {}, {}\n{}".format(time.time(), get_event_loop().time() - elapsed, get_event_loop().time(), elapsed, status_code, params.response))  # print data right away in the callback
    q.put([status_code, elapsed])


async def get_response(session, url, method="GET", data=None):
    #print("{}\n".format(url))
    if method.upper() != "POST":
        async with session.get(url) as resp:
            pass
    else:
        async with session.post(url, data) as resp:
            pass


def get_random_date_range(start_date, end_date, delta):
    epoch_start = start_date.timestamp()
    epoch_end = (end_date-delta).timestamp()
    # generate random number between (epoch_start) and (epoch_end-length)
    # convert random number in date and get date1
    date1 = datetime.fromtimestamp(random.randint(epoch_start, epoch_end))
    return "{}".format(date1.strftime("%Y-%m-%d"))

def print_report():
    # Change here for more complex reporting
    tot, succ = 0, 0
    for t in tasks:
        try:
            t.exception()
        except exceptions.InvalidStateError or client_exceptions.ServerDisconnectedError:
            pass
    while not q.empty():  # retrieve data from synchronized queue
        pair = q.get()
        q.task_done()
        # print(f'Latency: {pair[1]}, status: {pair[0]}')  # readable format
        # print(f'{pair[1]}, {pair[0]}, {op}, {url}')  # csv format
        if pair[0] == 200:
            succ += 1
        tot += pair[1]
    print(f'Avg Latency: {tot / count}, Success rate: {100 * succ / count}, Total requests: {count}', flush=True)
    # file.write(f'# Avg Latency: {tot / count}, Success rate: {100 * succ / count}\n')

def ctrl_c_handler(signum, frame):
    print_report()
    exit(1)

async def main():
    async with ClientSession(trace_configs=[trace_config]) as session:
        # TOTAL TIME MEASUREMENT
        start_time = get_event_loop().time()
        last = int(dim_dict["seconds"])
        distrib = dim_dict["distribution"]
        min_date = additional_dict["min_date"]
        max_date = additional_dict["max_date"]
        date_format = additional_dict["date_format"]
        elevation = int(additional_dict["elevation"])
        days = int(additional_dict["days"])
        min_lat = float(additional_dict["min_lat"])
        max_lat = float(additional_dict["max_lat"])
        min_lon = float(additional_dict["min_lon"])
        max_lon = float(additional_dict["max_lon"])
        min_offset = int(additional_dict["min_offset"])
        max_offset = int(additional_dict["max_offset"])
        if (distrib.lower() != "poisson" and distrib.lower() != "uniform"):
            printe("ERROR - Unknown distribution {}".format(distrib))
            exit(1)
        stress_test_last = start_time + last
        # tasks = set()
        global count
        print(f'"ts", "ts1", "ts2", "latency", "status"')
        op = req_dict["operation"]  # read from param if GET or POST
        base_url = req_dict["url"]  # read url from input param
        jpath = req_dict["payload"]  # eventually load json in case of http POST
        # csv_output = req_dict["csv"]  # output file for csv data UNUSED
        jcontent = None
        if op == "POST":
            jfile = open(jpath)
            jcontent = json.load(jfile)
            jfile.close()
        rps = int(dim_dict["rps"])  # read rps from input param
        while get_event_loop().time() < stress_test_last:  # replace with loop
            start_inner_loop_time = get_event_loop().time()
            date_range = get_random_date_range(datetime.strptime(min_date, date_format), datetime.strptime(max_date, date_format), timedelta(days=1))
            lat = random.uniform(min_lat + 0.0001, max_lat - 0.0001)
            lon = random.uniform(min_lon + 0.0001, max_lon - 0.0001)
            int_offset = random.randint(0, max_offset)
            offset = "{0:0=2d}".format(int_offset)
            int_offset = random.randint(min_offset, max_offset)
            if(int_offset >= 0):
              offset = "%2B" + offset
            else:
              offset = "-" + offset
            url = base_url + "elevation={}&date={}&offset={}:00&lat={}&lon={}&days={}".format(elevation, date_range, offset, round(lat, 4), round(lon, 4), days)
            task = create_task(get_response(session, url, op, jcontent))
            tasks.add(task)
            task.add_done_callback(tasks.discard)
            if(distrib.lower() == "poisson"):
                # Poisson
                slept, count = np.random.exponential(1 / rps), count + 1
            else:
                # Uniform
                slept, count = 1 / rps, count + 1
            await sleep(slept - (get_event_loop().time() - start_inner_loop_time))
            # print(f'slept: {slept}')  # print sleeping time
        print_report()
        #tot, succ = 0, 0
        #for t in tasks:
        #    try:
        #        t.exception()
        #    except exceptions.InvalidStateError or client_exceptions.ServerDisconnectedError:
        #        pass
        #while not q.empty():  # retrieve data from synchronized queue
        #    pair = q.get()
        #    q.task_done()
            # print(f'Latency: {pair[1]}, status: {pair[0]}')  # readable format
            # print(f'{pair[1]}, {pair[0]}, {op}, {url}')  # csv format
        #    if pair[0] == 200:
        #        succ += 1
        #    tot += pair[1]
        #print(f'Avg Latency: {tot / count}, Success rate: {100 * succ / count}')
        # file.write(f'# Avg Latency: {tot / count}, Success rate: {100 * succ / count}\n')


config = configparser.RawConfigParser()
if len(sys.argv) == 1:
    printe("ERROR - Missing configuration file")
    exit(1)
elif not genericpath.isfile(sys.argv[1]):
    printe("ERROR - Impossible to read configuration file")
    exit(1)
config.read(sys.argv[1])

try:
    req_dict = dict(config.items('REQUEST'))
    dim_dict = dict(config.items('DIMENSIONS'))
    additional_dict = dict(config.items('ADDITIONAL'))
except configparser.NoSectionError:
    printe("ERROR - Impossible to parse configuration file")
    exit(1)
trace_config = TraceConfig()
trace_config.on_request_start.append(on_request_start)
trace_config.on_request_end.append(on_request_end)

signal.signal(signal.SIGINT, ctrl_c_handler)
tasks = set()
count = 0
q = Queue()
run(main())
