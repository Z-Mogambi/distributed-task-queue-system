FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libpq-dev && \
    pip install --no-cache-dir -r requirements.txt && \
    rm -rf /var/lib/apt/lists/*

# Copy only the necessary application code
COPY task_queue/ ./task_queue/
COPY task_api/ ./task_api/

ENV PYTHONPATH=/app

ENTRYPOINT ["python"]
CMD ["task_api/server.py"]
