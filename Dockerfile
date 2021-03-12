FROM python:3.6-slim

# Force the stdout and stderr streams to be unbuffered.
# Ensure python output goes to your terminal
ENV PYTHONUNBUFFERED=1

WORKDIR /code
COPY requirements.txt /code/

RUN pip install -r requirements.txt

COPY . /code/
