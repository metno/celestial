FROM registry.met.no/baseimg/ubuntu:22.04

RUN apt-get update -y && \
    apt-get install -y python3-pip python3-dev python3


COPY requirements.txt /app/requirements.txt

RUN pip3 install --no-cache-dir --upgrade -r /app/requirements.txt

COPY ./app /app

# fix permissions
RUN chown -R 1000:1000 /app
WORKDIR /app

USER 1000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "2"]
