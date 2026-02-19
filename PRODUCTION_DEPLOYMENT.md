# Site Security Analyzer - Production Deployment Guide

## 🎯 Architecture Overview

```
                                    ┌─────────────────┐
                                    │   Users         │
                                    │  (100k+)        │
                                    └────────┬────────┘
                                             │
                                    ┌────────▼────────┐
                                    │   Nginx         │
                                    │   (Port 80)     │
                                    │   - Rate Limit  │
                                    │   - Load Balance│
                                    └────────┬────────┘
                                             │
                        ┌────────────────────┼────────────────────┐
                        │                    │                    │
                ┌───────▼──────┐    ┌───────▼──────┐    ┌───────▼──────┐
                │ Flask API    │    │ Flask API    │    │ Flask API    │
                │ Worker 1     │    │ Worker 2     │    │ Worker N     │
                │ (Gunicorn)   │    │ (Gunicorn)   │    │ (Gunicorn)   │
                └───────┬──────┘    └───────┬──────┘    └───────┬──────┘
                        │                    │                    │
                        └────────────────────┼────────────────────┘
                                             │
                        ┌────────────────────┼────────────────────┐
                        │                    │                    │
                ┌───────▼──────┐    ┌───────▼──────┐    ┌───────▼──────┐
                │ PostgreSQL   │    │   Redis      │    │  Celery      │
                │   (Primary)  │    │   - Cache    │    │  Workers     │
                │              │    │   - Queue    │    │  - Scanning  │
                │ (Replicas)   │    │   - Limits   │    │  - Cleanup   │
                └──────────────┘    └──────────────┘    └──────────────┘
                                             │
                        ┌────────────────────┼────────────────────┐
                        │                    │                    │
                ┌───────▼──────┐    ┌───────▼──────┐    ┌───────▼──────┐
                │ Prometheus   │    │  Grafana     │    │   Sentry     │
                │  (Metrics)   │    │(Dashboards)  │    │   (Errors)   │
                └──────────────┘    └──────────────┘    └──────────────┘
```

## 📋 Prerequisites

### System Requirements (for 100k users)

**Minimum**:
- 8 CPU cores
- 16 GB RAM
- 500 GB SSD storage
- 1 Gbps network

**Recommended**:
- 16 CPU cores
- 32 GB RAM
- 1 TB NVMe SSD
- 10 Gbps network

### Software Requirements
- Docker 20.10+
- Docker Compose 2.0+
- Python 3.11+ (for local testing)
- Node.js 18+ (for frontend build)

---

## 🚀 Quick Start (5 Minutes)

### 1. Clone and Configure

```bash
# Clone repository
git clone https://github.com/yourusername/site-security-analyzer.git
cd site-security-analyzer

# Generate secret key
python -c "import secrets; print(secrets.token_urlsafe(64))" > secret.txt

# Create environment file
cp .env.example .env

# Edit .env with your settings
nano .env
```

### 2. Configure Environment

Edit `.env` file:

```bash
# REQUIRED - Copy from secret.txt
SECRET_KEY=your-64-char-secret-key-here

# Database (auto-configured in docker-compose)
DATABASE_URL=postgresql://ssa_user:secure_password@postgres:5432/ssa_db
REDIS_URL=redis://redis:6379/0

# Frontend URL (update with your domain)
ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com

# Optional: Error Tracking
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project

# Optional: Email (for password reset)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
```

### 3. Launch Production Stack

```bash
# Start all services
docker-compose up -d

# Check service health
docker-compose ps

# View logs
docker-compose logs -f backend

# Initialize database
docker-compose exec backend flask db upgrade
```

### 4. Verify Deployment

```bash
# Check health endpoint
curl http://localhost/health

# Expected response:
# {"status":"healthy","database":"connected","redis":"connected","workers":8}

# Check metrics
curl http://localhost/metrics

# Check Grafana
# Open browser: http://localhost:3001
# Login: admin / admin
```

---

## 🔧 Detailed Configuration

### Database Setup

#### PostgreSQL Configuration

The default configuration supports ~10k concurrent users. For 100k users:

**docker-compose.yml** (update postgres service):
```yaml
postgres:
  image: postgres:15-alpine
  environment:
    POSTGRES_DB: ssa_db
    POSTGRES_USER: ssa_user
    POSTGRES_PASSWORD: secure_password
    # Tuning for 100k concurrent
    POSTGRES_SHARED_BUFFERS: 4GB
    POSTGRES_EFFECTIVE_CACHE_SIZE: 12GB
    POSTGRES_WORK_MEM: 16MB
  command: |
    postgres
    -c max_connections=1000
    -c shared_buffers=4GB
    -c effective_cache_size=12GB
    -c maintenance_work_mem=1GB
    -c checkpoint_completion_target=0.9
    -c wal_buffers=16MB
    -c default_statistics_target=100
    -c random_page_cost=1.1
```

#### Read Replicas (For Heavy Read Load)

Add to **docker-compose.yml**:
```yaml
postgres-replica:
  image: postgres:15-alpine
  environment:
    POSTGRES_PRIMARY_HOST: postgres
    POSTGRES_PRIMARY_PORT: 5432
    POSTGRES_USER: ssa_user
    POSTGRES_PASSWORD: secure_password
  command: |
    bash -c "
    until pg_basebackup --pgdata=/var/lib/postgresql/data -R --slot=replica1 --host=postgres --port=5432
    do
      echo 'Waiting for primary to be ready...'
      sleep 1s
    done
    echo 'Starting replica...'
    postgres
    "
```

Update `.env`:
```bash
DATABASE_REPLICA_URL=postgresql://ssa_user:secure_password@postgres-replica:5432/ssa_db
```

### Redis Configuration

For 100k users, enable Redis persistence and increase memory:

**docker-compose.yml**:
```yaml
redis:
  image: redis:7-alpine
  command: >
    redis-server
    --maxmemory 4gb
    --maxmemory-policy allkeys-lru
    --save 60 1000
    --appendonly yes
  volumes:
    - redis_data:/data
```

### Backend Scaling

#### Vertical Scaling (Single Server)

Update **start_production.sh**:
```bash
# Calculate workers: (2 x CPU) + 1
CPU_COUNT=$(nproc)
WORKERS=$((2 * CPU_COUNT + 1))

# For 16 CPU cores = 33 workers
# Each worker handles ~3k concurrent connections with gevent
# Total capacity: ~100k connections

gunicorn app_secure:app \
  --workers $WORKERS \
  --worker-class gevent \
  --worker-connections 3000 \
  --max-requests 10000 \
  --max-requests-jitter 1000 \
  --timeout 30 \
  --graceful-timeout 30 \
  --bind 0.0.0.0:5000
```

#### Horizontal Scaling (Multiple Servers)

**Server 1** (backend-01.yourdomain.com):
```bash
docker-compose up -d
```

**Server 2** (backend-02.yourdomain.com):
```bash
# Connect to same PostgreSQL and Redis
docker-compose -f docker-compose-worker.yml up -d
```

**Load Balancer** (nginx):
```nginx
upstream backend {
    least_conn;
    server backend-01.yourdomain.com:5000 max_fails=3 fail_timeout=30s;
    server backend-02.yourdomain.com:5000 max_fails=3 fail_timeout=30s;
    server backend-03.yourdomain.com:5000 max_fails=3 fail_timeout=30s;
    keepalive 64;
}
```

### Celery Worker Scaling

Scale workers based on scan volume:

```bash
# Scale to 10 workers (each handles ~100 concurrent scans)
docker-compose up -d --scale celery-worker=10

# Monitor queue length
docker-compose exec redis redis-cli llen celery

# If queue > 1000, add more workers
```

### Rate Limiting Tuning

Edit **nginx/nginx.conf**:

```nginx
# For authenticated premium users (higher limits)
limit_req_zone $jwt_claim_user_id zone=premium:10m rate=200r/s;

# General users
limit_req_zone $binary_remote_addr zone=general:10m rate=100r/s;

# Auth endpoints (prevent brute force)
limit_req_zone $binary_remote_addr zone=auth:10m rate=5r/m;

# Scan endpoint (prevent abuse)
limit_req_zone $binary_remote_addr zone=scan:10m rate=30r/h;
```

---

## 📊 Monitoring Setup

### Prometheus Queries

**Request Rate**:
```promql
sum(rate(http_requests_total[5m]))
```

**Error Rate**:
```promql
sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))
```

**Latency (p95)**:
```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

**Queue Length**:
```promql
celery_queue_length{queue="celery"}
```

### Grafana Dashboards

Import pre-built dashboards:
1. Open Grafana: http://localhost:3001
2. Login: admin / admin
3. Add Prometheus data source: http://prometheus:9090
4. Import dashboard ID: 12114 (Flask & Gunicorn)
5. Import dashboard ID: 2583 (PostgreSQL)
6. Import dashboard ID: 11835 (Redis)

### Alerts

Add to **monitoring/prometheus.yml**:

```yaml
alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']

rule_files:
  - /etc/prometheus/alerts.yml
```

Create **monitoring/alerts.yml**:

```yaml
groups:
  - name: ssa_alerts
    interval: 30s
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate: {{ $value }}%"
      
      # High latency
      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High p95 latency: {{ $value }}s"
      
      # Queue backup
      - alert: QueueBackup
        expr: celery_queue_length > 5000
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Celery queue backed up: {{ $value }} tasks"
      
      # Database connections exhausted
      - alert: DatabaseConnectionsHigh
        expr: pg_stat_activity_count / pg_settings_max_connections > 0.8
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Database connections at {{ $value }}% of max"
```

---

## 🧪 Load Testing

### Run Load Test

```bash
# Install Locust
pip install locust

# Run test (10k users for warmup)
locust -f load_test.py --users 10000 --spawn-rate 100 --run-time 10m --host http://localhost

# Full scale test (100k users)
locust -f load_test.py --users 100000 --spawn-rate 1000 --run-time 30m --host http://localhost
```

### Distributed Load Testing

On **Master** node:
```bash
locust -f load_test.py --master --expect-workers 4
```

On **Worker** nodes (4 machines):
```bash
locust -f load_test.py --worker --master-host <master-ip>
```

### Expected Performance Metrics

**Target SLAs for 100k concurrent users**:
- **Availability**: 99.9% uptime
- **Latency (p95)**: < 500ms
- **Latency (p99)**: < 2s
- **Error Rate**: < 0.1%
- **Throughput**: 50k requests/sec

**Results should show**:
```
Total Requests: 50,000,000
Failures: 5,000 (0.01%)
Median Response Time: 150ms
95th Percentile: 420ms
99th Percentile: 1.8s
Requests/sec: 52,000
```

---

## 🔐 Security Hardening

### SSL/TLS Setup

Generate certificates:
```bash
# Using Let's Encrypt
certbot certonly --standalone -d yourdomain.com

# Or self-signed (for testing)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/server.key \
  -out nginx/ssl/server.crt
```

Update **nginx/nginx.conf**:
```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /etc/nginx/ssl/server.crt;
    ssl_certificate_key /etc/nginx/ssl/server.key;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    
    # Other security headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Content-Security-Policy "default-src 'self'" always;
    
    location / {
        proxy_pass http://backend;
        # ... rest of config
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

### Firewall Rules

```bash
# Allow only necessary ports
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp      # SSH
ufw allow 80/tcp      # HTTP
ufw allow 443/tcp     # HTTPS
ufw enable
```

### Database Security

```sql
-- Create read-only user for replicas
CREATE USER ssa_readonly WITH PASSWORD 'readonly_password';
GRANT CONNECT ON DATABASE ssa_db TO ssa_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO ssa_readonly;

-- Revoke unnecessary permissions
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
```

### Regular Security Updates

```bash
# Weekly automated updates
cat > /etc/cron.weekly/security-updates <<EOF
#!/bin/bash
apt-get update
apt-get upgrade -y
docker-compose pull
docker-compose up -d
EOF

chmod +x /etc/cron.weekly/security-updates
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. **Database connection errors**

```bash
# Check database is running
docker-compose ps postgres

# Check connection
docker-compose exec postgres psql -U ssa_user -d ssa_db -c "SELECT 1;"

# View database logs
docker-compose logs postgres

# Increase max connections if needed
# Edit docker-compose.yml postgres command:
-c max_connections=500
```

#### 2. **Redis connection timeout**

```bash
# Check Redis is running
docker-compose ps redis

# Test connection
docker-compose exec redis redis-cli ping

# Check memory usage
docker-compose exec redis redis-cli info memory

# Increase memory if needed (docker-compose.yml)
--maxmemory 8gb
```

#### 3. **High CPU usage**

```bash
# Check which process is using CPU
docker stats

# Reduce number of workers if needed
# Edit start_production.sh:
WORKERS=16  # Instead of auto-calculated

# Or limit gevent connections per worker
--worker-connections 1000  # Instead of 3000
```

#### 4. **Celery tasks not processing**

```bash
# Check worker status
docker-compose exec celery-worker celery -A celery_tasks inspect active

# Check queue length
docker-compose exec redis redis-cli llen celery

# Restart workers
docker-compose restart celery-worker

# Scale up workers
docker-compose up -d --scale celery-worker=10
```

#### 5. **Rate limit errors**

```bash
# Check Nginx error log
docker-compose logs nginx | grep "limiting requests"

# Adjust limits in nginx/nginx.conf
limit_req_zone ... rate=200r/s;  # Increase from 100r/s

# Reload Nginx
docker-compose exec nginx nginx -s reload
```

### Debug Mode

Enable debug logging:

**.env**:
```bash
FLASK_DEBUG=True
LOG_LEVEL=DEBUG
```

Restart backend:
```bash
docker-compose restart backend
docker-compose logs -f backend
```

### Performance Profiling

Add to **app_secure.py**:
```python
from werkzeug.middleware.profiler import ProfilerMiddleware

if os.getenv('PROFILE'):
    app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[30])
```

Run with profiling:
```bash
PROFILE=1 docker-compose up backend
```

---

## 📦 Backup & Recovery

### Database Backup

```bash
# Daily automated backup
cat > /etc/cron.daily/postgres-backup <<EOF
#!/bin/bash
DATE=\$(date +%Y%m%d_%H%M%S)
docker-compose exec -T postgres pg_dump -U ssa_user ssa_db | gzip > /backups/ssa_db_\$DATE.sql.gz
# Keep only last 30 days
find /backups -name "ssa_db_*.sql.gz" -mtime +30 -delete
EOF

chmod +x /etc/cron.daily/postgres-backup
```

### Restore from Backup

```bash
# Stop backend (prevent writes)
docker-compose stop backend celery-worker

# Restore database
gunzip < /backups/ssa_db_20240115_120000.sql.gz | \
  docker-compose exec -T postgres psql -U ssa_user ssa_db

# Restart services
docker-compose start backend celery-worker
```

### Redis Backup

```bash
# Redis automatically saves to disk (RDB + AOF enabled)
# Manual backup:
docker-compose exec redis redis-cli BGSAVE

# Copy RDB file
docker cp $(docker-compose ps -q redis):/data/dump.rdb /backups/redis_dump.rdb
```

---

## 🚀 Deployment Checklist

Before going to production:

- [ ] Generate strong `SECRET_KEY` (64+ characters)
- [ ] Update `ALLOWED_ORIGINS` with production domain
- [ ] Configure SSL/TLS certificates
- [ ] Set up database backups (daily)
- [ ] Configure Sentry error tracking
- [ ] Set up monitoring alerts
- [ ] Run load test (100k users)
- [ ] Review and tune rate limits
- [ ] Configure email (SMTP) for password reset
- [ ] Update frontend `VITE_API_URL` environment variable
- [ ] Update extension `API_URL` and `APP_URL`
- [ ] Set up firewall rules
- [ ] Enable database read replicas (if needed)
- [ ] Configure CDN for static assets (optional)
- [ ] Set up log rotation
- [ ] Document runbooks for common issues
- [ ] Train team on monitoring dashboards

---

## 📞 Support

For issues or questions:
- GitHub Issues: https://github.com/yourusername/site-security-analyzer/issues
- Documentation: https://docs.yourdomain.com
- Discord: https://discord.gg/yourserver

---

**Next**: See [SECURITY_FIXES.md](SECURITY_FIXES.md) for detailed security improvements.
