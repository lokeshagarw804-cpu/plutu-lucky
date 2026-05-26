FROM ghcr.io/laude-institute/t-bench/python:latest
WORKDIR /app
RUN pip install --no-cache-dir pytest || true
COPY runtime/ /app/runtime/
