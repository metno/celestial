FROM python:3.8.13-bullseye

COPY config.cfg config.cfg
COPY src/requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY src/main.py src/main.py

ENTRYPOINT [ "python", "src/main.py", "config.cfg" ]
