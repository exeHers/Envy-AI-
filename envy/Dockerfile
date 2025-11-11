FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

RUN python -m venv /app/.venv \
    && . /app/.venv/bin/activate \
    && pip install --upgrade pip \
    && pip install ".[dev]" \
    && bash scripts/download_models.sh

EXPOSE 8420
CMD ["/bin/bash", "-c", "source /app/.venv/bin/activate && python -m envy.main start --no-gui"]
