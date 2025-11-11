FROM python:3.10-slim

ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        espeak \
        portaudio19-dev \
        git \
        build-essential && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

RUN python -m venv .venv && \
    . .venv/bin/activate && \
    pip install --upgrade pip && \
    pip install --no-cache-dir . && \
    python scripts/download_models.py --profile balanced --root /app

EXPOSE 8765

CMD ["python", "-m", "envy.cli", "run", "--profile", "balanced", "--dashboard"]
