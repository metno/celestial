# What is Sunrise?
Sunrise is a small application for calculating the astronomical phenomena such the rising and setting of the moon.
The purpose of this project is to provide an endpoint for delivering information of said phenomenas to end users such as yr.no.

## Who is responsible?
Responsible for this repository is Håkon Tansem (haakont@met.no)

## Status
This project is currently under development.

# Getting started

## Test it out
Note: The first request each time the application is started in docker may take a few more seconds than normal. This is because the application has to download a table containing positional information for astronomical objects.
### Prerequisites
Sunrise is a python application utilizing the fastapi web framework library.
The application requires python3>=3.6
The library requirements are as follows
- fastapi>=0.73.0
- numpy>=1.19.5
- skyfield>=1.43.1
- uvicorn>=0.16.0
- pytz>=2021.3
- lxml>=4.8.0
- jinja2>=3.0.3

These are also listed in the `requirements.txt` file.
Older versions may work, but are not tested.

### Running with docker
In order to run the application, type `docker-compose up`.
This requires docker-compose. (This is currently only tested on Docker Compose version v2.6.1)


## Documentation
Api spec for the application is generated and can be viewed on the `/docs` endpoint when running this application. Here it is described how to make http requests to the application.
For calculating astronomical positions of the Moon and Sun relative to the Earth, the skyfield library ([https://rhodesmill.org/skyfield/](https://rhodesmill.org/skyfield/)) is used. Please refer to
its documentation when viewing the code for this application.  

# How to contribute
If you want to contribute to this project, please create a fork or a branch and start a subsequent merge request explaining why you think your change is necessary.
You can also contact Håkon Tansem (haakont@met.no) directly if you have proposed changes for this project.
This code utilises python with fastapi as the web framework library. For more information on fastapi check out this [link](https://fastapi.tiangolo.com/).
The main engine for calculating the astronomical phenomena is through the skyfield library for Python. Check out the documentation [here](https://rhodesmill.org/skyfield/) or the subsequent github [repository](https://github.com/skyfielders/python-skyfield).
For work on this project, the following "arbeidsordre" is used: Sunrise (157160303).
