FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    ENVY_HOME=/opt/envy

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 python3-venv python3-pip \
        build-essential \
        curl wget git \
        portaudio19-dev \
        libasound2 libasound2-dev \
        ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR ${ENVY_HOME}
COPY . ${ENVY_HOME}

RUN python3 -m venv ${ENVY_HOME}/venv && \
    ${ENVY_HOME}/venv/bin/pip install --upgrade pip && \
    ${ENVY_HOME}/venv/bin/pip install -e ${ENVY_HOME}

EXPOSE 8080

ENTRYPOINT ["./start-envy.sh"]
CMD ["--profile", "balanced"]
