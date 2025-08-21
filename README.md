# PDF-Processing-Pipeline-FastAPI-Celery-Apache-Tika-RabbitMQ-Redis-Dockerized-
A fully containerized PDF text-extraction pipeline built with FastAPI, Celery, RabbitMQ, Apache Tika, and Redis.

## Stack
- Apache Tika (text extraction) — `:9998`
- RabbitMQ (broker) — `:5672`, management UI `:15672`
- Redis (result store) — `:6379`
- FastAPI (API) — `:8000`
- Celery worker(s)

## Quick start
```bash
# from project root
mkdir -p uploads

# bring everything up
docker compose up --build -d

# view logs
docker compose logs -f