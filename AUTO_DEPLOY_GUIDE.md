# Auto-Deploy from GitHub

## 🚀 Option 1: Railway.app (Recommended - Easiest)

### Setup (5 minutes)

1. **Sign up at Railway.app**
   ```
   https://railway.app
   ```

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Connect your GitHub account
   - Select this repository

3. **Configure Environment Variables**
   ```
   ANTHROPIC_API_KEY=sk-ant-xxxxx
   API_SECRET_KEY=<generate-random>
   DATABASE_URL=<leave empty, Railway provides>
   ```

4. **Deploy Settings**
   - Railway auto-detects `railway.toml`
   - Uses Dockerfile automatically
   - Provisions PostgreSQL if needed

5. **Done!**
   - Every push to `main` auto-deploys
   - Railway provides URL: `https://your-app.up.railway.app`

### Cost
- **Free tier**: $5 credit/month
- **Typical usage**: $3-8/month
- **Persistent volumes included**

---

## 🚀 Option 2: Render.com (Good Free Tier)

### Setup (7 minutes)

1. **Sign up at Render.com**
   ```
   https://render.com
   ```

2. **New Web Service**
   - Connect GitHub repo
   - Select "Docker"
   - Render detects `render.yaml`

3. **Environment Variables**
   ```
   ANTHROPIC_API_KEY=sk-ant-xxxxx
   API_SECRET_KEY=<generate>
   ```

4. **Persistent Disk**
   - Render auto-creates from `render.yaml`
   - 1GB free persistent storage

5. **Deploy**
   - Auto-deploys on push to main
   - URL: `https://your-app.onrender.com`

### Cost
- **Free tier**: Available (spins down after 15 min idle)
- **Starter**: $7/month (always on)

---

## 🚀 Option 3: Fly.io (Most Powerful)

### Setup (10 minutes)

1. **Install Fly CLI**
   ```bash
   # macOS/Linux
   curl -L https://fly.io/install.sh | sh

   # Windows
   iwr https://fly.io/install.ps1 -useb | iex
   ```

2. **Login & Launch**
   ```bash
   fly auth login
   fly launch

   # Answer prompts:
   # - App name: competitor-ad-analyzer
   # - Region: Choose nearest
   # - PostgreSQL: No (using SQLite for now)
   # - Deploy: Yes
   ```

3. **Set Secrets**
   ```bash
   fly secrets set ANTHROPIC_API_KEY=sk-ant-xxxxx
   fly secrets set API_SECRET_KEY=$(openssl rand -hex 32)
   ```

4. **Auto-Deploy from GitHub**
   ```bash
   fly deploy --remote-only

   # Add GitHub Action (already created in .github/workflows/)
   # Push to main → auto-deploys
   ```

### Cost
- **Free tier**: 3 VMs, 3GB storage
- **Typical**: $0-5/month

---

## 📊 Error Monitoring (Sentry)

### Setup Sentry (5 minutes)

1. **Sign up at Sentry.io**
   ```
   https://sentry.io/signup/
   ```

2. **Create Project**
   - Platform: Python/FastAPI
   - Copy DSN: `https://xxxxx@xxxxx.ingest.sentry.io/xxxxx`

3. **Add to Environment Variables**

   **Railway:**
   ```bash
   # In Railway dashboard
   SENTRY_DSN=https://xxxxx@xxxxx.ingest.sentry.io/xxxxx
   ENVIRONMENT=production
   ```

   **Render:**
   ```bash
   # In Render dashboard under Environment
   SENTRY_DSN=https://xxxxx@xxxxx.ingest.sentry.io/xxxxx
   ```

   **Fly:**
   ```bash
   fly secrets set SENTRY_DSN=https://xxxxx@xxxxx.ingest.sentry.io/xxxxx
   ```

4. **Install Sentry Package**
   ```bash
   pip install sentry-sdk[fastapi]
   # Already in requirements.txt
   ```

5. **Enable in API** (Update `api/server.py`):
   ```python
   from core.sentry import setup_sentry

   # At startup
   @app.on_event("startup")
   async def startup():
       setup_sentry()
   ```

6. **Configure Alerts**
   - Sentry dashboard → Alerts
   - Set email notifications for:
     - New errors
     - Error rate spikes
     - Performance issues

### What You'll Get
- 📧 **Email alerts** on errors
- 📊 **Error tracking** with stack traces
- 🔍 **Performance monitoring**
- 👥 **User context** (who hit the error)
- 🕐 **Error trends** over time

---

## 🔔 Setting Up Notifications

### Slack Notifications

1. **Create Slack Webhook**
   ```
   https://api.slack.com/messaging/webhooks
   ```

2. **Add to GitHub Secrets**
   - Go to: `https://github.com/your-username/your-repo/settings/secrets`
   - Add: `SLACK_WEBHOOK = https://hooks.slack.com/services/xxxxx`

3. **GitHub Actions will notify on**:
   - ✅ Successful deploys
   - ❌ Failed deploys
   - ⚠️ Test failures

### Email Notifications

**Sentry automatically sends emails for:**
- New errors
- Error rate increases
- Performance regressions

**Configure in Sentry:**
- Settings → Notifications
- Add your email
- Set thresholds

---

## 🔄 Auto-Deploy Workflow

### What Happens on `git push`

```
1. Push to GitHub (main branch)
   ↓
2. GitHub Actions run
   ├─ Run tests
   ├─ Build Docker image
   └─ Notify if failures
   ↓
3. Platform detects push (Railway/Render/Fly)
   ├─ Pull latest code
   ├─ Build Docker image
   ├─ Run database migrations
   └─ Deploy new version
   ↓
4. Health check
   ├─ If healthy: ✅ Deploy complete
   └─ If unhealthy: ❌ Rollback + alert
   ↓
5. Sentry monitors for errors
   └─ Email you if issues detected
```

### Rollback on Failure

**Railway:**
```bash
# View deployments
railway status

# Rollback to previous
railway rollback
```

**Render:**
```bash
# In dashboard, click "Rollback" on previous deploy
```

**Fly:**
```bash
# List releases
fly releases

# Rollback
fly releases rollback <version>
```

---

## 🧪 Testing Before Deploy

### Local Testing
```bash
# Test Docker build
docker build -t test-app .
docker run -p 8000:8000 test-app

# Run tests
pytest tests/ -v

# Check health
curl http://localhost:8000/health
```

### Staging Environment
```bash
# Create staging branch
git checkout -b staging

# Deploy to staging (separate Railway/Render app)
# Push to staging branch → deploys to staging URL

# Test on staging
curl https://staging-app.railway.app/health

# If good, merge to main
git checkout main
git merge staging
git push  # Auto-deploys to production
```

---

## 💰 Cost Breakdown

### Railway (Recommended)
| Feature | Free Tier | Paid |
|---------|-----------|------|
| Apps | Unlimited | Unlimited |
| Credit | $5/month | Pay as you go |
| DB | Included | PostgreSQL |
| Deploy | Auto | Auto |
| Cost | ~$0-5/mo | ~$5-15/mo |

### Render
| Feature | Free Tier | Starter |
|---------|-----------|---------|
| Web Service | ✅ (spins down) | Always on |
| Storage | 1GB | 1GB+ |
| Deploy | Auto | Auto |
| Cost | $0 | $7/month |

### Fly.io
| Feature | Free Tier | Paid |
|---------|-----------|------|
| VMs | 3 free | Pay per VM |
| Storage | 3GB | Pay per GB |
| Deploy | Auto | Auto |
| Cost | ~$0 | ~$5-10/mo |

### Sentry
| Feature | Free | Paid |
|---------|------|------|
| Events | 5k/month | Unlimited |
| Projects | 1 | Unlimited |
| Team | 1 user | Team |
| Cost | $0 | $26/month |

**Total Minimum Cost: $0-7/month**

---

## 🚨 About "Sending Errors to Me"

### The Reality
I (Claude) **cannot** receive:
- ❌ Emails
- ❌ Slack messages
- ❌ API calls
- ❌ Any real-time notifications

### What I CAN Help With
When you share error logs, I can:
- ✅ Debug the error
- ✅ Suggest fixes
- ✅ Write patches
- ✅ Update code

### How to Get Help
1. **Check Sentry** for errors
2. **Copy error details**
3. **Paste in conversation**
4. **I'll analyze and fix**

---

## 📝 Quick Deploy Checklist

### Before First Deploy
- [ ] Sign up for Railway/Render/Fly
- [ ] Sign up for Sentry (optional but recommended)
- [ ] Set ANTHROPIC_API_KEY in platform
- [ ] Generate and set API_SECRET_KEY
- [ ] Connect GitHub repository
- [ ] Configure auto-deploy

### After First Deploy
- [ ] Visit deployed URL
- [ ] Test `/health` endpoint
- [ ] Get JWT token
- [ ] Make test API call
- [ ] Trigger error to test Sentry
- [ ] Verify email notifications work

### Ongoing
- [ ] Monitor Sentry for errors
- [ ] Check deploy status after pushes
- [ ] Review cost monthly
- [ ] Keep dependencies updated

---

## 🎯 Recommended Setup

For most users:
1. **Deploy on**: Railway.app (easiest)
2. **Errors**: Sentry.io (free tier)
3. **Notifications**: Sentry email alerts
4. **Cost**: $5-10/month total

---

Need help with any step? Just ask and I'll guide you through it!
