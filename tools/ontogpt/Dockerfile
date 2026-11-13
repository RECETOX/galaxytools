# Image used by the Galaxy tool: recetox/ontogpt:1.2.0-recetox1
# Built from the upstream uv.lock so that the tested dependency resolution is used.
FROM python:3.12-slim
ARG ONTOGPT_VERSION=1.2.0
RUN apt-get update && apt-get install -y --no-install-recommends git procps && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir uv
RUN git clone --depth 1 --branch v${ONTOGPT_VERSION} https://github.com/monarch-initiative/ontogpt /opt/ontogpt
WORKDIR /opt/ontogpt
RUN uv export --frozen --no-dev --no-emit-project -o /tmp/requirements.txt \
    && pip install --no-cache-dir -r /tmp/requirements.txt \
    && pip install --no-cache-dir --no-deps .
