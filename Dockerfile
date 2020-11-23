FROM golang:alpine3.11 AS builder

RUN apk --no-cache add git && git clone https://github.com/Andrew-Morozko/cloudy-uploader.git && cd cloudy-uploader && go build

FROM tiangolo/meinheld-gunicorn-flask:python3.8-alpine3.11

COPY --from=builder /go/cloudy-uploader/cloudy-uploader /usr/local/bin
