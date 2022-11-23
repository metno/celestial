FROM python:3.12-rc

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

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
#CMD ["hypercorn", "main:app", "--bind", "0.0.0.0:8080"]
