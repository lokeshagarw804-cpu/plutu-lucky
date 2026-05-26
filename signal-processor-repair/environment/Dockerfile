FROM python:3.11-slim
RUN pip install uv
COPY runtime/ /app/runtime/
WORKDIR /app
ENTRYPOINT []
USER root
RUN mkdir -p /logs/verifier \
 && echo 0 > /logs/verifier/reward.txt \
 && chmod -R 0777 /logs
RUN mkdir -p /app/runtime/output
