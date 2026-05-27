FROM python:3.10-slim

RUN pip install --no-cache-dir pytest

WORKDIR /app

# Copy runtime files
COPY runtime/ /app/environment/runtime/

# Copy tests
COPY ../tests/ /app/tests/

# Copy instruction
COPY ../instruction.md /app/instruction.md

# Default command runs the pipeline
CMD ["python", "environment/runtime/run_pipeline.py"]
