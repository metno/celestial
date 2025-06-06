FROM registry.met.no/baseimg/ubuntu:24.04

RUN apt-get update -y && \
    apt-get install -y python3-pip python3-dev python3.12-venv


COPY requirements.txt /app/requirements.txt

RUN python3 -m venv venv && \
    . venv/bin/activate && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt


COPY ./app /app

# fix permissions
RUN chown -R 1000:1000 /app
WORKDIR /app

USER 1000

CMD ["/bin/bash", "-c", ". ../venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8080 --workers 2 --no-access-log"]
