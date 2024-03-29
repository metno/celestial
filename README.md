# Celestial

## What is Celestial?

Celestial is a small application for calculating the astronomical phenomena such the rising and setting of The Sun and The Moon.
The purpose of this application is to serve as an endpoint for the sunrise 3.0 endpoint at api.met.no. (<https://api.met.no/weatherapi/sunrise/3.0/documentation>)

### Who is responsible?

Responsible for this repository is Håkon Tansem (haakont@met.no)

### Status

This product is operational. It serves as a backend for the sunrise 3.0 product on api.met.no.
(see https://api.met.no/weatherapi/sunrise/3.0/documentation)
## Getting started

### Test it out

#### Prerequisites

Celestial is a python application utilizing the fastapi web framework library.
The application requires python3>=3.8
For the docker image specified in the compose file, Python 3.11 is used.
The library requirements are as follows

- fastapi==0.90.1
- numpy>=1.19.5
- skyfield>=1.43.1
- uvicorn>=0.16.0
- prometheus-fastapi-instrumentator>=5.9.1

These are also listed in the `requirements.txt` file.
Older versions may work, but are not tested.

#### Running with docker

In order to run the application, type `docker-compose up`.
This requires docker-compose. (This is currently only tested on Docker Compose version v2.6.1).

### Documentation

Api spec for the application is generated and can be viewed on the `/docs` endpoint when running this application. Here it is described how to make http requests to the application.
For calculating the rising and setting times of the Moon and the Sun, the skyfield library ([https://rhodesmill.org/skyfield/](https://rhodesmill.org/skyfield/)) is used. Please refer to
its documentation when viewing the code for this application.  

### How to contribute

If you want to contribute to this project, please create a fork or a branch and start a subsequent merge request explaining why you think your change is necessary.
You can also contact Håkon Tansem (haakont@met.no) directly if you have proposed changes for this project.
This code utilises python with fastapi as the web framework library. For more information on fastapi check out this [link](https://fastapi.tiangolo.com/).
The main engine for calculating the astronomical phenomena is through the skyfield library for Python. Check out the documentation [here](https://rhodesmill.org/skyfield/) or the subsequent github [repository](https://github.com/skyfielders/python-skyfield).

### Tests

To run integration tests:

- Install tox in your venv: ```pip3 install tox```
- Run ```tox```.

```bash
tox
```

To run quality control (note that external APIs are used):

- ```pip3 install -r test_requirements```
- ```python3 app/quality_control.py```

```bash
python3 quality_control.py
```
