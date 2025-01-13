FROM golang:1 AS builder

RUN apt-get update && apt-get install -y git && git clone https://github.com/Andrew-Morozko/cloudy-uploader.git && cd cloudy-uploader && go build && rm -rf /var/lib/apt/lists/*

FROM tiangolo/meinheld-gunicorn-flask:python3.9

WORKDIR /app
COPY --from=builder /go/cloudy-uploader/cloudy-uploader /app/cloudy-uploader
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*
COPY ./app /app
RUN pip3 install -r requirements.txt
