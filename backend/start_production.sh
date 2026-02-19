#!/bin/sh
# Production startup script for backend

# Exit on error
set -e

# Validate required environment variables
if [ -z "$SECRET_KEY" ] || [ ${#SECRET_KEY} -lt 64 ]; then
    echo "ERROR: SECRET_KEY must be set and at least 64 characters"
    exit 1
fi

if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL must be set"
    exit 1
fi

# Run database migrations
echo "Running database migrations..."
flask db upgrade || echo "No migrations to run"

# Calculate optimal worker count: (2 x CPU cores) + 1
WORKERS=${GUNICORN_WORKERS:-$(($(nproc 2>/dev/null || echo 2) * 2 + 1))}

echo "Starting Gunicorn with $WORKERS workers on port ${PORT:-5000}"

exec gunicorn app_secure:app \
    --bind "0.0.0.0:${PORT:-5000}" \
    --workers "$WORKERS" \
    --worker-class gevent \
    --worker-connections 1000 \
    --timeout 30 \
    --graceful-timeout 30 \
    --keep-alive 5 \
    --max-requests 10000 \
    --max-requests-jitter 1000 \
    --access-logfile - \
    --error-logfile - \
    --access-logformat '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s' \
    --log-level info \
    --preload \
    --enable-stdio-inheritance
