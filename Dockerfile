# syntax=docker/dockerfile:1.4
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
WORKDIR /app

COPY set-up/requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
	pip install -r requirements.txt

COPY src ./src
ENV PYTHONPATH=/app/src/main
CMD ["python", "src/main/pipeline.py"]
