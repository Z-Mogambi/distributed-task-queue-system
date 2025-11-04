FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY task_queue/ ./task_queue/
COPY task_workers/ ./task_workers/
COPY task_api/ ./task_api/

# Set Python path so imports work
ENV PYTHONPATH=/app

# Default command (will be overridden by Render)
CMD ["python", "task_api/server.py"]