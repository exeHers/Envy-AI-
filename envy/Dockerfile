FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENVY_PROFILE=balanced \
    ENVY_CONFIG_PATH=/opt/envy/config/envy.yaml

WORKDIR /opt/envy

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md LICENSE /opt/envy/
COPY config /opt/envy/config
COPY src /opt/envy/src
COPY scripts /opt/envy/scripts
COPY start-envy.sh run_envy_local.sh /opt/envy/

RUN pip install --upgrade pip && pip install -e ".[dev]"
RUN chmod +x /opt/envy/start-envy.sh /opt/envy/run_envy_local.sh /opt/envy/scripts/download_models.sh

RUN /opt/envy/scripts/download_models.sh --demo

EXPOSE 8201 8202 8203 8204 8205 8300

ENTRYPOINT ["/opt/envy/run_envy_local.sh", "--profile", "balanced", "--no-gui"]
