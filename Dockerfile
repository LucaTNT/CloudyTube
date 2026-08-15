FROM golang:1.22-alpine AS builder

RUN apk add --no-cache git && \
    git clone --branch v1.1.2 --depth 1 https://github.com/Andrew-Morozko/cloudy-uploader.git && \
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

RUN useradd --no-create-home --shell /usr/sbin/nologin appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8080

HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/')" || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--no-control-socket", "main:app"]
