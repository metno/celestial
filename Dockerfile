FROM ubuntu:jammy

RUN apt-get update -y && \
    apt-get install -y python3-pip python3-dev python3


COPY requirements.txt /app/requirements.txt
COPY ./app /app

# fix permissions

RUN pip3 install -r /app/requirements.txt


RUN chown -R 1000:1000 /app
WORKDIR /app

# lastly
USER 1000


CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "16"]
