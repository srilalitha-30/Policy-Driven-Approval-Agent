# Deployment Guide

## Production Deployment

### Prerequisites
- Python 3.9+ (3.14 is supported)
- Node.js 16+ (for frontend, optional)
- SQLite3 (included with Python)
- A web server (nginx, Apache) for reverse proxy

### Backend Deployment

#### 1. Using Gunicorn (Production WSGI Server)

```bash
cd backend

# Install production dependencies
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 -k uvicorn.workers.UvicornWorker main:app
```

#### 2. Using Docker

Create a `Dockerfile` in the backend directory:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "-k", "uvicorn.workers.UvicornWorker", "main:app"]
```

Build and run:

```bash
docker build -t approval-agent .
docker run -p 8000:8000 approval-agent
```

#### 3. Using Systemd (Linux)

Create `/etc/systemd/system/approval-agent.service`:

```ini
[Unit]
Description=Policy-Driven Approval Agent
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/var/www/approval-agent/backend
Environment="PATH=/var/www/approval-agent/backend/venv/bin"
ExecStart=/var/www/approval-agent/backend/venv/bin/gunicorn \
    -w 4 -b 0.0.0.0:8000 \
    -k uvicorn.workers.UvicornWorker main:app

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable approval-agent
sudo systemctl start approval-agent
```

### Frontend Deployment

#### 1. Build for Production

```bash
cd frontend
npm run build
```

This creates an optimized build in the `build/` directory.

#### 2. Serve with Node

```bash
npm install -g serve
serve -s build -p 3000
```

#### 3. Serve with nginx

Configure nginx reverse proxy:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
    }

    # API
    location /api/ {
        proxy_pass http://localhost:8000/;
    }
}
```

### Database

#### SQLite (Development/Small Scale)
- Default configuration uses SQLite
- Database file: `approval_agent.db`
- No additional setup required
- Good for prototypes and small deployments

#### PostgreSQL (Production)

1. Install PostgreSQL and create a database:

```bash
createdb approval_agent
```

2. Update environment variable:

```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/approval_agent"
```

3. The app uses SQLAlchemy, so it will work with any supported database

### Environment Variables

Create a `.env` file in the backend directory:

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False

# Database
DATABASE_URL=sqlite:///./approval_agent.db

# Security (optional)
OPENAI_API_KEY=sk-... (for future LLM enhancements)
```

### Performance Optimization

1. **Enable Caching**
   ```python
   from fastapi_cache2 import FastAPICache2
   from fastapi_cache2.backends.redis import RedisBackend
   ```

2. **Use Connection Pooling**
   ```python
   engine = create_engine(
       DATABASE_URL,
       pool_size=20,
       max_overflow=40
   )
   ```

3. **Enable Compression**
   ```python
   from fastapi.middleware.gzip import GZIPMiddleware
   app.add_middleware(GZIPMiddleware, minimum_size=1000)
   ```

4. **Rate Limiting**
   ```python
   from slowapi import Limiter
   from slowapi.util import get_remote_address
   limiter = Limiter(key_func=get_remote_address)
   app.state.limiter = limiter
   ```

### Monitoring & Logging

1. **Application Logging**
   ```python
   import logging
   logging.basicConfig(level=logging.INFO)
   ```

2. **Sentry Integration**
   ```bash
   pip install sentry-sdk
   ```

3. **Prometheus Metrics**
   ```bash
   pip install prometheus-client
   ```

### Security Checklist

- ✅ Use HTTPS in production
- ✅ Set `DEBUG=False`
- ✅ Use strong database passwords
- ✅ Implement authentication/authorization
- ✅ Enable CORS only for trusted origins
- ✅ Use environment variables for secrets
- ✅ Regularly update dependencies
- ✅ Implement rate limiting
- ✅ Use a Web Application Firewall (WAF)

### Backup Strategy

1. **Database Backups**
   ```bash
   # SQLite
   cp approval_agent.db approval_agent.db.backup
   
   # PostgreSQL
   pg_dump approval_agent > backup.sql
   ```

2. **Automated Backups** (Cron job)
   ```cron
   0 2 * * * /path/to/backup-script.sh
   ```

### Health Checks

The application provides a health check endpoint:

```bash
curl http://localhost:8000/health
# Response: {"status":"healthy"}
```

Monitor this endpoint to ensure the service is running.

### Scaling

For higher traffic:

1. **Horizontal Scaling**
   - Run multiple backend instances behind a load balancer
   - Use a shared database (PostgreSQL recommended)

2. **Caching Layer**
   - Add Redis for session and query caching

3. **Async Processing**
   - Use Celery for long-running tasks

4. **Database Optimization**
   - Add indexes on frequently queried fields
   - Archive old evaluations

## Migration Guide

If migrating from another system:

1. **Export data** from the old system
2. **Transform** to the expected format
3. **Import** via the API:
   ```bash
   for rule in rules.json; do
       curl -X POST http://localhost:8000/rules -d "$rule"
   done
   ```
4. **Validate** by running sample evaluations
5. **Monitor** for discrepancies

## Support

For issues or questions:
1. Check the README.md
2. Review the QUICK_START.md
3. Check application logs
4. Open an issue on GitHub
