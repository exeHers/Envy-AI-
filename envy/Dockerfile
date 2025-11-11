FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENVY_HOME=/opt/envy

WORKDIR ${ENVY_HOME}

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    portaudio19-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY . ${ENVY_HOME}

RUN pip install --upgrade pip setuptools wheel \
    && pip install -e ".[dev]" \
    && SKIP_LLM_DOWNLOAD=1 python scripts/download_models.py

EXPOSE 8190

CMD ["python", "-m", "envy.cli", "start", "--profile", "balanced", "--headless"]
