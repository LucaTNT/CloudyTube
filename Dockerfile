FROM golang:alpine3.11 AS builder

RUN apk --no-cache add git && git clone https://github.com/Andrew-Morozko/cloudy-uploader.git && cd cloudy-uploader && go build

FROM tiangolo/meinheld-gunicorn-flask:python3.8-alpine3.11

WORKDIR /app
COPY --from=builder /go/cloudy-uploader/cloudy-uploader /app/cloudy-uploader
RUN apk --no-cache add ffmpeg
COPY ./app /app
RUN pip3 install -r requirements.txt
