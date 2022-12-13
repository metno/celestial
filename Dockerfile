FROM python:3.12-rc

COPY requirements.txt /app/requirements.txt

RUN pip3 install --no-cache-dir --upgrade -r /app/requirements.txt

COPY ./app /app

# fix permissions
RUN chown -R 1000:1000 /app
WORKDIR /app

USER 1000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "2"]
