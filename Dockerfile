# Multi-stage Dockerfile for openHASP Designer
# Stage 1: Build frontend (placeholder - will be added when frontend is ready)
# Stage 2: Python backend

FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY backend-python/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend-python/app ./app

# Create necessary directories
RUN mkdir -p /data /config

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8080/api/status')" || exit 1

# Run with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
