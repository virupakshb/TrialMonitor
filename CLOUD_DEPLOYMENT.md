# 🚀 Cloud Deployment Guide
## Clinical Trial Data Layer - NVX-1218.22

This guide shows you how to deploy your clinical trial API to free cloud platforms in just a few minutes.

---

## 📋 What You're Deploying

- **SQLite Database**: 2.81 MB with 17,511 clinical trial records
- **FastAPI Backend**: REST API with 20+ endpoints
- **No external dependencies**: Self-contained database
- **Production-ready**: CORS enabled, health checks included

---

## 🎯 Deployment Options (All Free Tier)

### Option 1: Railway (Recommended - Easiest) ⭐

**Pros:**
- Easiest deployment (3 clicks)
- Automatic HTTPS
- 500 hours/month free
- Fast cold starts

**Steps:**

1. **Install Railway CLI** (optional, can also use web)
   ```bash
   npm install -g @railway/cli
   ```

2. **Login to Railway**
   ```bash
   railway login
   ```

3. **Initialize and Deploy**
   ```bash
   cd clinical-trial-data-layer
   railway init
   railway up
   ```

4. **Get your URL**
   ```bash
   railway domain
   ```

**Your API is live!** 🎉

**Web Alternative (No CLI needed):**
1. Go to https://railway.app
2. Click "New Project"
3. Choose "Deploy from GitHub repo"
4. Connect your repo (or upload files)
5. Railway auto-detects and deploys
6. Get your URL from the dashboard

**Cost:** Free for 500 hours/month, then $5/month

---

### Option 2: Render (100% Free Forever)

**Pros:**
- Free forever tier
- Automatic SSL
- GitHub integration
- No credit card needed

**Cons:**
- Slower cold starts (sleeps after 15 min inactivity)

**Steps:**

1. **Create account at https://render.com**

2. **Click "New +" → "Web Service"**

3. **Connect your GitHub repo** (or upload files)

4. **Configure:**
   - **Name:** clinical-trial-api
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn api_sqlite:app --host 0.0.0.0 --port $PORT`
   - **Plan:** Free

5. **Click "Create Web Service"**

**Your API is live in 2-3 minutes!** 🎉

**Cost:** $0 forever

---

### Option 3: Fly.io (Global Edge Deployment)

**Pros:**
- Deploy to multiple regions
- Fast globally
- Great free tier
- Docker-based

**Steps:**

1. **Install Fly CLI**
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Login**
   ```bash
   fly auth login
   ```

3. **Launch app**
   ```bash
   cd clinical-trial-data-layer
   fly launch
   ```

4. **Answer prompts:**
   - App name: clinical-trial-api
   - Region: Choose closest to you
   - Postgres: No (we use SQLite)
   - Deploy: Yes

**Your API is live globally!** 🎉

**Cost:** Free for 3 apps, 160GB bandwidth/month

---

### Option 4: Docker (Any Cloud Platform)

If you want to deploy to AWS, Google Cloud, Azure, DigitalOcean, etc:

1. **Build Docker image**
   ```bash
   docker build -t clinical-trial-api .
   ```

2. **Test locally**
   ```bash
   docker run -p 8000:8000 clinical-trial-api
   ```

3. **Deploy to your cloud:**
   - **AWS ECS/Fargate:** Push to ECR, create service
   - **Google Cloud Run:** `gcloud run deploy`
   - **Azure Container Apps:** `az containerapp up`
   - **DigitalOcean App Platform:** Connect repo, auto-deploy

---

## 🧪 Testing Your Deployment

Once deployed, test your API:

```bash
# Replace YOUR_URL with your actual deployment URL

# Health check
curl https://YOUR_URL/

# Get statistics
curl https://YOUR_URL/api/statistics

# Get all sites
curl https://YOUR_URL/api/sites

# Get serious adverse events
curl https://YOUR_URL/api/adverse-events?seriousness=Yes

# Get subject data
curl https://YOUR_URL/api/subjects/101-001
```

**Interactive API Docs:**
Visit `https://YOUR_URL/docs` for full Swagger documentation

---

## 📊 Quick Comparison

| Platform | Free Tier | Setup Time | Cold Start | Best For |
|----------|-----------|------------|------------|----------|
| **Railway** | 500 hrs/mo | 2 min | Fast | Quick demos |
| **Render** | Forever | 3 min | Slow | Long-term free |
| **Fly.io** | 3 apps | 5 min | Fast | Global access |
| **Docker** | Varies | 10 min | Varies | Custom clouds |

---

## 🔧 Environment Variables (If Needed)

Most platforms auto-detect `$PORT`. If you need to configure:

```env
PORT=8000
PYTHON_VERSION=3.11
```

For Railway/Render, these are usually automatic.

---

## 📱 Connect Your Frontend

Once deployed, use your API URL in frontend apps:

```javascript
// React example
const API_URL = 'https://your-app.railway.app';

fetch(`${API_URL}/api/subjects`)
  .then(res => res.json())
  .then(data => console.log(data));
```

---

## 🔄 Updating Your Deployment

**Railway:**
```bash
railway up
```

**Render:**
- Push to GitHub → Auto-deploys

**Fly.io:**
```bash
fly deploy
```

**Docker:**
```bash
docker build -t clinical-trial-api .
# Push to your registry and redeploy
```

---

## 🔒 Security Best Practices

### For Production Deployments:

1. **Enable HTTPS** (all platforms do this automatically)
2. **Add authentication** if needed:
   ```python
   # Add to api_sqlite.py
   from fastapi.security import HTTPBearer
   security = HTTPBearer()
   ```
3. **Rate limiting**:
   ```bash
   pip install slowapi
   ```
4. **Database backup**: Download `clinical_trial.db` regularly

---

## 💡 Pro Tips

### Make Database Read-Only (Optional)
```python
# In api_sqlite.py, add when opening connection:
conn = sqlite3.connect(DB_PATH, check_same_thread=False, uri=True)
conn.execute("PRAGMA query_only = ON")
```

### Add Caching for Performance
```bash
pip install fastapi-cache2
```

### Monitor Your API
- Railway: Built-in metrics
- Render: Dashboard metrics
- Fly.io: `fly logs`

---

## 🆘 Troubleshooting

**"Port already in use"**
```bash
# Change port in command:
uvicorn api_sqlite:app --port 8001
```

**"Database locked"**
- SQLite has limitations with concurrent writes
- For production with many users, upgrade to PostgreSQL

**"Module not found"**
```bash
# Reinstall dependencies:
pip install -r requirements.txt
```

**Cold starts too slow on Render?**
- Render free tier sleeps after 15 minutes
- First request wakes it up (takes ~30 seconds)
- Consider Railway or Fly.io for faster cold starts

---

## 📈 Scaling Beyond Free Tier

### When to Upgrade:

**Railway ($5/month):**
- After 500 hours/month
- Need faster response times
- More control

**Render ($7/month):**
- Need always-on service
- No sleep on inactivity

**Fly.io ($0-10/month):**
- Need multiple regions
- High traffic

### Migration to PostgreSQL:

When you need better concurrency:

1. Use Supabase (500MB free)
2. Run the original `load_data.py` script
3. Switch to `api.py` (PostgreSQL version)
4. Update deployment to use PostgreSQL connection

---

## ✅ Quick Deployment Checklist

- [ ] Choose platform (Railway recommended)
- [ ] Create account
- [ ] Upload/connect repository
- [ ] Deploy (auto or CLI)
- [ ] Test API endpoints
- [ ] Share URL with team
- [ ] Set up monitoring (optional)

---

## 🎉 You're Done!

Your clinical trial monitoring API is now live on the internet, serving real data from a production database.

**Next Steps:**
- Build a frontend dashboard
- Add AI monitoring agents
- Set up alerts and notifications
- Create data visualizations

---

**Questions?** Check the main README.md or API documentation at `/docs`

**Protocol:** NVX-1218.22  
**Sponsor:** NexaVance Therapeutics Inc.  
**Version:** 1.0
