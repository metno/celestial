FROM python:3.11

COPY requirements.txt /app/requirements.txt
COPY ./app /app

# fix permissions

RUN pip3 install -r /app/requirements.txt


RUN chown -R 1000:1000 /app
WORKDIR /app

# lastly
USER 1000

# compile python
RUN python3 -m compileall /app

CMD ["python3", "/app/__pycache__/main.cpython-311.pyc"]
