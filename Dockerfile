FROM ubuntu:jammy

RUN apt-get update -y && \
    apt-get install -y python3-pip python3-dev python3


COPY requirements.txt /app/requirements.txt
COPY ./app /app

RUN pip3 install -r /app/requirements.txt

WORKDIR /app
USER nobody:nogroup

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]

