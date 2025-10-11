# Backend Dockerfile for Cloud Run
FROM python:3.11-slim

# Prevents Python from writing .pyc files and enables unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

# Install system deps (optional, kept minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Expose the port (for documentation)
EXPOSE 8080

# Use gunicorn in production; Cloud Run sends $PORT
CMD ["gunicorn", "-b", ":8080", "--workers", "1", "--threads", "8", "--timeout", "0", "app:app"]
