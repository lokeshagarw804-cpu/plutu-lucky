FROM ghcr.io/laude-institute/t-bench/base:latest

RUN apt-get update && apt-get install -y jq

COPY runtime/ /environment/runtime/

RUN mkdir -p /output

WORKDIR /environment
