FROM node:22-bookworm-slim AS upstream

RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

ARG OPENKB_REF=ff54396e575ee6feb0113b631a34caa082b441cc
RUN git clone https://github.com/VectifyAI/OpenKB.git /opt/openkb \
    && git -C /opt/openkb checkout --detach "${OPENKB_REF}"
WORKDIR /opt/openkb/frontend
RUN npm ci && npm run build && rm -rf node_modules

FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    OPENKB_KB_ROOT=/data/kbs
RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*
COPY --from=upstream /opt/openkb /opt/openkb
RUN pip install --no-cache-dir "/opt/openkb[web]"
COPY bootstrap.py /app/bootstrap.py
COPY source_pages.py /app/source_pages.py
WORKDIR /app
EXPOSE 7566
CMD ["python", "/app/bootstrap.py"]
