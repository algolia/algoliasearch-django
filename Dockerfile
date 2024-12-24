FROM python:3.13-slim

# Force the stdout and stderr streams to be unbuffered.
# Ensure python output goes to your terminal
ENV PYTHONUNBUFFERED=1

WORKDIR /code
COPY requirements.txt /code/

RUN pip3 install --upgrade pip && pip3 install -r requirements.txt

COPY . /code/
