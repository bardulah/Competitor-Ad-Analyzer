# Production Deployment Guide

## ⚠️ **Current Status: Beta - Production-Ready Features**

This guide covers deploying the **working, tested features** of the Competitor Ad Analyzer.

### ✅ What Actually Works (Tested)

1. **Database Layer** - SQLAlchemy ORM with migrations
2. **Configuration Management** - Pydantic-based validation
3. **Error Handling** - Custom exception hierarchy
4. **Integration Tests** - Real database tests
5. **Docker Deployment** - Full containerization
6. **API Authentication** - JWT-based security
7. **Basic Scraping** - Synchronous scrapers (original implementation)

### 🚧 What Needs More Testing

1. **Async Scrapers** - Built but not fully tested in production
2. **Video Analysis** - Requires ffmpeg and additional setup
3. **Cost Tracking** - Estimates work, real tracking needs validation
4. **Monitoring System** - Email alerts not fully implemented
5. **Caching** - Database caching works, Redis integration pending

### ❌ What's Not Production-Ready

1. **Official API Integration** - Requires Facebook API approval
2. **DALL-E Creative Generation** - Placeholder only
3. **Celery Background Tasks** - Not configured
4. **Multi-tenant Support** - Single user only

---

## Prerequisites

### Required
- Docker & Docker Compose
- **Anthropic API Key** (Claude) - [Get one here](https://console.anthropic.com/)
- 4GB RAM minimum
- 10GB disk space

### Optional
- OpenAI API Key (for future DALL-E integration)
- PostgreSQL (for production scale)
- Redis (for caching)

---

## Quick Start (Docker)

### 1. Clone and Configure

```bash
git clone <repository-url>
cd Competitor-Ad-Analyzer

# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env
```

### 2. Set Required Environment Variables

```bash
# .env file
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx
API_SECRET_KEY=your-random-secret-key-change-me
```

### 3. Deploy with Docker Compose

```bash
# Build and start
docker-compose up -d

# Check logs
docker-compose logs -f app

# Access API docs
open http://localhost:8000/docs
```

### 4. Create Admin User (First Time)

```bash
# Generate password hash
docker-compose exec app python -c "
from api.auth import get_password_hash
print(get_password_hash('your-password-here'))
"

# Add to api/auth.py fake_users_db with your hash
```

### 5. Get Access Token

```bash
curl -X POST "http://localhost:8000/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=secret"

# Response:
# {
#   "access_token": "eyJ...",
#   "token_type": "bearer"
# }
```

### 6. Make Authenticated Request

```bash
# Use the token in Authorization header
curl -H "Authorization: Bearer eyJ..." \
  http://localhost:8000/stats
```

---

## Production Deployment (Manual)

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### 2. Setup Database

```bash
# Run migrations
alembic upgrade head

# Verify
python -c "
from database import get_db
db = get_db()
print('Database connection successful!')
"
```

### 3. Configure Environment

```bash
# Create .env file
cat > .env << EOF
ANTHROPIC_API_KEY=your-key-here
DATABASE_URL=sqlite:///./data/competitor_ads.db
API_SECRET_KEY=$(openssl rand -hex 32)
LOG_LEVEL=INFO
MAX_SESSION_COST=10.0
EOF
```

### 4. Run API Server

```bash
# Development
uvicorn api.server:app --reload

# Production (with gunicorn)
gunicorn api.server:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

### 5. Setup Systemd Service (Linux)

```bash
# Create service file
sudo tee /etc/systemd/system/ad-analyzer.service > /dev/null <<EOF
[Unit]
Description=Competitor Ad Analyzer API
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/competitor-ad-analyzer
Environment="PATH=/opt/competitor-ad-analyzer/venv/bin"
ExecStart=/opt/competitor-ad-analyzer/venv/bin/gunicorn api.server:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000

[Install]
WantedBy=multi-user.target
EOF

# Start service
sudo systemctl daemon-reload
sudo systemctl enable ad-analyzer
sudo systemctl start ad-analyzer
```

---

## Configuration Reference

### Core Settings (core/config.py)

```python
# API Keys (REQUIRED)
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Database
DATABASE_URL=sqlite:///./data/competitor_ads.db
# For PostgreSQL:
# DATABASE_URL=postgresql://user:pass@localhost/competitor_ads

# Security
API_SECRET_KEY=your-secret-key  # Generate with: openssl rand -hex 32
API_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Scraping
MAX_CONCURRENT_REQUESTS=3
REQUEST_TIMEOUT=30
RATE_LIMIT_DELAY=2
BROWSER_HEADLESS=true

# Analysis
MIN_AD_QUALITY_SCORE=5.0
ENABLE_VISUAL_ANALYSIS=true
USE_QUICK_FILTER=true

# Cost Limits
MAX_SESSION_COST=10.0
WARN_COST_THRESHOLD=5.0

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/ad-analyzer/app.log
```

---

## Running Tests

### Unit & Integration Tests

```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=. --cov-report=html

# Skip live API tests
pytest tests/ -v -m "not liveapi"

# Run only integration tests
pytest tests/test_integration.py -v
```

### Manual API Testing

```bash
# Health check
curl http://localhost:8000/health

# Get statistics
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/stats

# Estimate cost
curl -X POST http://localhost:8000/estimate-cost \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"num_ads": 50, "analyze_visual": true}'
```

---

## Monitoring & Maintenance

### Health Checks

```bash
# Check API health
curl http://localhost:8000/health

# Check database
docker-compose exec app python -c "
from database import get_session
session = get_session()
print(f'DB connected: {session is not None}')
"
```

### Logs

```bash
# Docker logs
docker-compose logs -f app

# Application logs
tail -f logs/app.log

# Error logs only
docker-compose logs app | grep ERROR
```

### Database Maintenance

```bash
# Backup database
cp data/competitor_ads.db data/backup_$(date +%Y%m%d).db

# Clean old ads (older than 90 days)
docker-compose exec app python -c "
from database import AdRepository
with AdRepository() as repo:
    deleted = repo.delete_old_ads(days=90)
    print(f'Deleted {deleted} old ads')
"

# Check database size
du -h data/competitor_ads.db
```

### Cost Monitoring

```bash
# Get cost report
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/cost-report?days=30"

# Example response:
# {
#   "period_days": 30,
#   "total_cost": 15.43,
#   "breakdown": {
#     "visual_analysis": 10.25,
#     "messaging_analysis": 3.18,
#     "other": 2.00
#   }
# }
```

---

## Troubleshooting

### Common Issues

#### 1. "No module named 'playwright'"
```bash
pip install playwright
playwright install chromium
```

#### 2. "ANTHROPIC_API_KEY not found"
```bash
# Check .env file exists
cat .env | grep ANTHROPIC

# Set manually
export ANTHROPIC_API_KEY=sk-ant-xxxxx
```

#### 3. "Database is locked"
```bash
# SQLite limitation - use PostgreSQL for production
# Or reduce concurrent operations
```

#### 4. "401 Unauthorized"
```bash
# Token expired - get new one
curl -X POST "http://localhost:8000/token" \
  -d "username=admin&password=secret"
```

#### 5. "Playwright browser not found"
```bash
# Reinstall browsers
playwright install chromium --force
```

---

## Security Checklist

- [ ] Change `API_SECRET_KEY` from default
- [ ] Use strong passwords for users
- [ ] Enable HTTPS in production (use nginx/traefik)
- [ ] Restrict CORS origins (not `allow_origins=["*"]`)
- [ ] Set up firewall rules
- [ ] Regular database backups
- [ ] Monitor API usage and costs
- [ ] Keep dependencies updated
- [ ] Use PostgreSQL instead of SQLite for production
- [ ] Set up rate limiting per user

---

## Performance Tips

1. **Use PostgreSQL** - SQLite has concurrency limitations
2. **Enable Caching** - Set up Redis for analysis caching
3. **Limit Scraping** - Start with 10-20 ads, not 100+
4. **Use Quick Filter** - Saves ~50% on analysis costs
5. **Schedule Off-Peak** - Run large jobs during low-cost hours
6. **Monitor Costs** - Set up alerts at $5, $10 thresholds

---

## What to Monitor

### Key Metrics
- API response times
- Database query performance
- API cost per day/week/month
- Scraping success/failure rates
- Cache hit rates
- Disk space usage

### Recommended Tools
- **Logging**: Built-in Python logging to file
- **Monitoring**: Prometheus + Grafana (future)
- **Alerts**: Set up cost alerts via API
- **Backups**: Daily cron job for database

---

## Scaling Considerations

### Current Limitations
- SQLite: ~100 concurrent reads, 1 concurrent write
- Single instance: No load balancing
- No distributed caching
- File-based screenshots: Limited by disk I/O

### To Scale Beyond 1000 Ads/Day
1. **Switch to PostgreSQL** - Handle concurrent writes
2. **Add Redis** - Distributed caching
3. **Use S3/Cloud Storage** - For screenshots
4. **Add Load Balancer** - Multiple API instances
5. **Celery Workers** - Background job processing
6. **CDN** - For serving reports/screenshots

---

## Support & Maintenance

### Regular Tasks
- **Daily**: Check logs for errors
- **Weekly**: Review cost reports
- **Monthly**: Database backup and cleanup
- **Quarterly**: Update dependencies

### Getting Help
- Check logs first: `docker-compose logs -f app`
- Run integration tests: `pytest tests/test_integration.py -v`
- Review configuration: `core/config.py`
- Check API docs: `http://localhost:8000/docs`

---

## License & Legal

- Respect platform Terms of Service
- Do not overload ad libraries
- Use rate limiting (built-in)
- Competitive research only, not ad copying
- Comply with advertising regulations

---

**Last Updated**: 2025-01-06
**Version**: 2.0.0
**Status**: Production Beta
