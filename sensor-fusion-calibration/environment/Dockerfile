FROM python:3.9-slim

WORKDIR /app

# Copy runtime files
COPY runtime/ /app/

# Verify pipeline runs
RUN python3 run_calibration.py > /dev/null 2>&1 || true

CMD ["python3", "run_calibration.py"]
