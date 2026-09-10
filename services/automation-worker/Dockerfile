# syntax=docker/dockerfile:1.7
# AnderZilla Automation Worker — private Cloud Run, scale-to-zero (min 0)
# Base pinned by digest for reproducibility (linux/amd64 manifest). Regenerate with:
#   docker buildx imagetools inspect python:3.12-slim-bookworm --format '{{json .Manifest.Digest}}'
FROM --platform=linux/amd64 python:3.12-slim-bookworm@sha256:9c47360a2a0355e2da18516d0b1c2126ec22c195d2185e97347c9d98398c5bef

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py ./

# Non-root user
RUN useradd -m -u 10001 worker && chown -R worker:worker /app
USER worker

ENV PORT=8080
EXPOSE 8080

# Cloud Run sends $PORT; uvicorn binds 0.0.0.0:$PORT with single worker (scale-to-zero, request-based)
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1 --no-access-log --log-level info"]
