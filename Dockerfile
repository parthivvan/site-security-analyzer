# Railway Dockerfile - deploys backend
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Copy backend files
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./

# Railway sets PORT automatically
EXPOSE 8080

# Use shell form to allow variable expansion
CMD gunicorn -b 0.0.0.0:${PORT:-8080} --workers 1 --threads 8 --timeout 0 app:app
