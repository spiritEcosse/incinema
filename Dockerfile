FROM python:3.11.7

RUN apt update
RUN apt install -y \
  libavformat-dev \
  libavdevice-dev \
  libavfilter-dev \
  libswscale-dev \
  ffmpeg

RUN mkdir -p /app
WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .
