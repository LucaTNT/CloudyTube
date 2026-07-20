FROM golang:1.22-alpine AS builder

RUN apk add --no-cache git && \
    git clone https://github.com/Andrew-Morozko/cloudy-uploader.git && \
    cd cloudy-uploader && \
    go build

FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY --from=builder /go/cloudy-uploader/cloudy-uploader /app/cloudy-uploader

RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg nodejs && \
    rm -rf /var/lib/apt/lists/*

COPY ./app /app
RUN python -m pip install --upgrade pip && \
    python -m pip install --no-cache-dir -r requirements.txt

EXPOSE 80

CMD ["gunicorn", "--bind", "0.0.0.0:80", "main:app"]
