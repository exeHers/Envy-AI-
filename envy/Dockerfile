FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential libportaudio2 curl unzip && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /opt/envy

COPY . .

RUN pip install --upgrade pip && \
    pip install . && \
    bash scripts/download_models.sh --minimal

EXPOSE 7000 7001 7002 7003 7004 7005 7010

CMD ["python", "-m", "envy", "--profile", "balanced"]
