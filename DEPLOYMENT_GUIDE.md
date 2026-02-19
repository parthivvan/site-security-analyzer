# 🚀 Deployment Guide - Site Security Analyzer

This guide covers deploying the Site Security Analyzer to various cloud platforms for production use.

## 📋 Table of Contents
1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Environment Configuration](#environment-configuration)
3. [Frontend Deployment](#frontend-deployment)
4. [Backend Deployment](#backend-deployment)
5. [Database Setup](#database-setup)
6. [Domain & SSL](#domain--ssl)
7. [Monitoring & Maintenance](#monitoring--maintenance)

---

## ✅ Pre-Deployment Checklist

Before deploying, ensure:

- [ ] All tests pass locally
- [ ] Environment variables are documented
- [ ] Database migrations are ready
- [ ] API endpoints are tested
- [ ] Security headers are configured
- [ ] Rate limiting is enabled
- [ ] CORS origins are set correctly
- [ ] Secrets are stored securely (not in code)
- [ ] Build scripts work without errors
- [ ] README and docs are updated

---

## 🔧 Environment Configuration

### Frontend Environment Variables

Create `.env.production`:

```env
VITE_API_URL=https://your-backend-api.com
VITE_WS_URL=wss://your-backend-api.com
VITE_APP_NAME=Site Security Analyzer
VITE_VERSION=2.0.0
```

### Backend Environment Variables

Create `.env.production`:

```env
# Flask/FastAPI
SECRET_KEY=your-super-secret-key-change-in-production
DATABASE_URL=postgresql://user:password@host:5432/dbname
ALLOWED_ORIGINS=https://your-frontend.com,https://www.your-frontend.com

# Optional: Email notifications
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Optional: Analytics
GOOGLE_ANALYTICS_ID=UA-XXXXXXXXX-X
```

**⚠️ IMPORTANT**: Never commit `.env` files to Git!

---

## 🌐 Frontend Deployment

### Option 1: Vercel (Recommended)

**Why Vercel?**
- Zero-config deployment
- Automatic HTTPS
- Edge CDN
- Free tier available

**Steps:**

1. Install Vercel CLI:
```bash
npm install -g vercel
```

2. Login and deploy:
```bash
cd frontend
vercel login
vercel --prod
```

3. Configure:
- Add environment variables in Vercel dashboard
- Set build command: `npm run build`
- Set output directory: `dist`
- Add custom domain

**Alternative: GitHub Integration**
1. Push code to GitHub
2. Connect repo to Vercel
3. Auto-deploys on every push to main

---

### Option 2: Firebase Hosting

**Why Firebase?**
- Google infrastructure
- Free SSL
- CDN included
- Easy rollbacks

**Steps:**

1. Install Firebase CLI:
```bash
npm install -g firebase-tools
```

2. Login and initialize:
```bash
firebase login
firebase init hosting
```

3. Configure `firebase.json`:
```json
{
  "hosting": {
    "public": "frontend/dist",
    "ignore": ["firebase.json", "**/.*", "**/node_modules/**"],
    "rewrites": [
      {
        "source": "**",
        "destination": "/index.html"
      }
    ],
    "headers": [
      {
        "source": "**",
        "headers": [
          {
            "key": "X-Content-Type-Options",
            "value": "nosniff"
          },
          {
            "key": "X-Frame-Options",
            "value": "SAMEORIGIN"
          },
          {
            "key": "X-XSS-Protection",
            "value": "1; mode=block"
          }
        ]
      }
    ]
  }
}
```

4. Build and deploy:
```bash
cd frontend
npm run build
firebase deploy --only hosting
```

---

### Option 3: Netlify

**Why Netlify?**
- Drag-and-drop deployment
- Form handling
- Split testing
- Functions support

**Steps:**

1. Build project:
```bash
cd frontend
npm run build
```

2. Deploy via web interface:
- Go to [netlify.com](https://netlify.com)
- Drag `dist` folder to deploy zone
- Or connect GitHub repo

3. Configure in `netlify.toml`:
```toml
[build]
  command = "npm run build"
  publish = "dist"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200

[[headers]]
  for = "/*"
  [headers.values]
    X-Frame-Options = "SAMEORIGIN"
    X-Content-Type-Options = "nosniff"
    X-XSS-Protection = "1; mode=block"
```

---

## 🔌 Backend Deployment

### Option 1: Railway (Recommended)

**Why Railway?**
- PostgreSQL included
- Auto-scaling
- Simple CLI
- Free tier: 500 hours/month

**Steps:**

1. Install Railway CLI:
```bash
npm install -g @railway/cli
```

2. Login and initialize:
```bash
railway login
railway init
```

3. Link PostgreSQL:
```bash
railway add postgresql
```

4. Deploy:
```bash
cd backend
railway up
```

5. Add environment variables:
```bash
railway variables set SECRET_KEY=your-secret-key
railway variables set DATABASE_URL=${{POSTGRES.DATABASE_URL}}
```

6. Configure start command:
- In `railway.json`:
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "gunicorn app:app --bind 0.0.0.0:$PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

---

### Option 2: Render

**Why Render?**
- Free PostgreSQL
- Auto-deploy from Git
- Free SSL
- Background workers

**Steps:**

1. Create `render.yaml`:
```yaml
services:
  - type: web
    name: security-analyzer-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app --bind 0.0.0.0:$PORT
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: security-analyzer-db
          property: connectionString
      - key: SECRET_KEY
        generateValue: true
      - key: PYTHON_VERSION
        value: 3.9.0

databases:
  - name: security-analyzer-db
    databaseName: security_db
    user: security_user
```

2. Push to GitHub

3. Connect to Render:
- Go to [render.com](https://render.com)
- New -> Blueprint
- Connect repository
- Deploy

---

### Option 3: Heroku

**Steps:**

1. Install Heroku CLI:
```bash
npm install -g heroku
```

2. Create app:
```bash
heroku create security-analyzer-api
```

3. Add PostgreSQL:
```bash
heroku addons:create heroku-postgresql:hobby-dev
```

4. Set environment variables:
```bash
heroku config:set SECRET_KEY=your-secret-key
heroku config:set ALLOWED_ORIGINS=https://your-frontend.com
```

5. Create `Procfile`:
```
web: gunicorn app:app --log-file=-
```

6. Deploy:
```bash
git push heroku main
```

---

### Option 4: Docker Deployment

**For any cloud provider (AWS, DigitalOcean, etc.)**

1. Build Docker image:
```bash
cd backend
docker build -t security-analyzer:latest .
```

2. Test locally:
```bash
docker run -p 5000:5000 \
  -e SECRET_KEY=test \
  -e DATABASE_URL=postgresql://... \
  security-analyzer:latest
```

3. Push to registry:
```bash
docker tag security-analyzer:latest your-registry/security-analyzer:latest
docker push your-registry/security-analyzer:latest
```

4. Deploy to cloud:
- AWS ECS/Fargate
- Google Cloud Run
- DigitalOcean App Platform
- Azure Container Instances

---

## 🗄️ Database Setup

### PostgreSQL (Production)

**Railway:**
```bash
# Automatically provisioned
railway add postgresql
```

**Manual setup:**
```sql
-- Create database
CREATE DATABASE security_analyzer;

-- Create user
CREATE USER security_user WITH PASSWORD 'secure_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE security_analyzer TO security_user;

-- Connect and run migrations
psql -U security_user -d security_analyzer -f migrations/schema.sql
```

### Migration Script

Create `backend/migrations/init.sql`:
```sql
-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Scans table
CREATE TABLE IF NOT EXISTS scans (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    target VARCHAR(500) NOT NULL,
    scan_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_scans_user_id ON scans(user_id);
CREATE INDEX idx_scans_created_at ON scans(created_at DESC);
```

Run migration:
```bash
psql $DATABASE_URL -f migrations/init.sql
```

---

## 🌐 Domain & SSL

### Custom Domain Setup

**Frontend (Vercel/Netlify):**
1. Go to domain settings
2. Add your domain: `yourdomain.com`
3. Configure DNS:
   - Type: `A`
   - Name: `@`
   - Value: Provider's IP
   - Or use CNAME for `www`

**Backend (Railway/Render):**
1. Go to settings
2. Add custom domain
3. Update DNS:
   - Type: `CNAME`
   - Name: `api`
   - Value: `your-app.railway.app`

### SSL Certificate
- **Automatic**: Most platforms provide free SSL (Let's Encrypt)
- **Manual**: Upload certificate in platform settings

---

## 📊 Monitoring & Maintenance

### Application Monitoring

**Sentry (Error Tracking)**
```bash
npm install @sentry/react
```

```javascript
// frontend/src/main.jsx
import * as Sentry from "@sentry/react";

Sentry.init({
  dsn: "your-sentry-dsn",
  environment: "production",
  tracesSampleRate: 1.0,
});
```

**Backend:**
```python
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[FlaskIntegration()],
    traces_sample_rate=1.0
)
```

### Performance Monitoring

**Google Analytics**
```html
<!-- frontend/index.html -->
<script async src="https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'GA_MEASUREMENT_ID');
</script>
```

### Health Checks

Add health endpoint:
```python
@app.route('/health')
def health():
    return {'status': 'healthy', 'timestamp': datetime.now().isoformat()}
```

### Backup Strategy

**Automated Database Backups:**
```bash
# Daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump $DATABASE_URL > backups/backup_$DATE.sql
aws s3 cp backups/backup_$DATE.sql s3://your-bucket/backups/
```

**Cron job:**
```bash
0 2 * * * /path/to/backup.sh
```

---

## 🔒 Security Checklist

Before going live:

- [ ] HTTPS enabled everywhere
- [ ] Environment variables not in code
- [ ] Rate limiting enabled
- [ ] CORS properly configured
- [ ] SQL injection prevention (use ORM)
- [ ] XSS protection headers set
- [ ] CSRF tokens implemented
- [ ] Input validation on all forms
- [ ] Error messages don't leak info
- [ ] Dependencies updated
- [ ] Security audit performed
- [ ] Penetration testing done

---

## 📈 Scaling Considerations

### For High Traffic:

1. **Frontend:**
   - Use CDN (Cloudflare)
   - Enable caching
   - Optimize images (WebP)
   - Code splitting
   - Lazy loading

2. **Backend:**
   - Add Redis for caching
   - Use load balancer
   - Database connection pooling
   - Queue system (Celery/BullMQ)
   - Horizontal scaling

3. **Database:**
   - Read replicas
   - Connection pooling
   - Query optimization
   - Indexing strategy

---

## 🆘 Troubleshooting

### Common Issues:

**CORS Errors:**
```python
# backend/app.py
CORS(app, resources={
    r"/*": {
        "origins": ["https://your-frontend.com"],
        "methods": ["GET", "POST"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})
```

**Database Connection:**
```python
# Check connection string format
# PostgreSQL: postgresql://user:pass@host:port/dbname
# Add ?sslmode=require for production
```

**Build Errors:**
```bash
# Clear cache
rm -rf node_modules dist
npm install
npm run build
```

---

## ✅ Post-Deployment Checklist

- [ ] Frontend accessible via HTTPS
- [ ] Backend API responding
- [ ] Database connected
- [ ] Authentication working
- [ ] Scans completing successfully
- [ ] Email notifications sent
- [ ] Browser extension connects
- [ ] Error tracking configured
- [ ] Analytics recording
- [ ] Backups scheduled
- [ ] Monitoring alerts set
- [ ] Documentation updated
- [ ] Team notified

---

## 🎉 You're Live!

Congratulations on deploying your security analyzer! Remember to:

1. Monitor error logs daily
2. Update dependencies monthly
3. Review security patches weekly
4. Backup database regularly
5. Test disaster recovery plan
6. Collect user feedback
7. Plan feature updates

---

**Need Help?**
- Check platform documentation
- Review error logs
- Search Stack Overflow
- Ask in project Discord/Slack
- Open GitHub issue

**Good luck with your deployment! 🚀**
