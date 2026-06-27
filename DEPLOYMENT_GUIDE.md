# HK Shipping - Complete Deployment Guide

## Step 1: Create Requirements File (Dependencies)
Before pushing to GitHub, create a `requirements.txt` file with all dependencies:

```
Flask==2.3.0
Werkzeug==2.3.0
gunicorn==21.2.0
```

## Step 2: Create .gitignore File
Create a `.gitignore` file to exclude sensitive files:

```
__pycache__/
*.pyc
*.pyo
*.db
.env
.venv
venv/
env/
*.log
.DS_Store
instance/
.pytest_cache/
.coverage
htmlcov/
dist/
build/
*.egg-info/
```

## Step 3: Initialize Git Repository Locally

```bash
cd "c:\Users\sathw\OneDrive\Desktop\Transport Invoice & Payment Tracker-1"
git init
git add .
git commit -m "Initial commit: HK Shipping Flask application"
```

## Step 4: Create GitHub Repository

1. Go to https://github.com/new
2. Create a new repository named `hk-shipping-tracker` (or your choice)
3. Do NOT initialize with README, .gitignore, or license (we already have these)
4. Click "Create repository"

## Step 5: Add Remote and Push to GitHub

```bash
git remote add origin https://github.com/YOUR_USERNAME/hk-shipping-tracker.git
git branch -M main
git push -u origin main
```

## Step 6: Choose Your Deployment Platform

### Option A: Deploy to Render (Recommended - Free Tier Available)

**Step 6A-1:** Go to https://render.com and sign up

**Step 6A-2:** Connect your GitHub account
- Click "New +" → "Web Service"
- Select your GitHub repository
- Click "Connect"

**Step 6A-3:** Configure the deployment:
- **Name:** hk-shipping-tracker
- **Environment:** Python 3
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn app:app`
- **Instance Type:** Free (or paid if needed)

**Step 6A-4:** Add environment variables:
- Click "Environment"
- Add any needed variables (Flask_ENV=production, etc.)

**Step 6A-5:** Deploy
- Click "Create Web Service"
- Wait for deployment (2-3 minutes)
- Get your live URL: `https://hk-shipping-tracker.onrender.com`

---

### Option B: Deploy to Railway (Simple & Free)

**Step 6B-1:** Go to https://railway.app and sign up with GitHub

**Step 6B-2:** Create new project
- Click "New Project" → "Deploy from GitHub"
- Select your repository

**Step 6B-3:** Configure:
- Railway auto-detects Python
- Add `Procfile` file to root (see below)
- Deploy automatically starts

**Procfile contents:**
```
web: gunicorn app:app
```

---

### Option C: Deploy to Heroku (Free tier ended, but still viable)

**Step 6C-1:** Sign up at https://www.heroku.com

**Step 6C-2:** Create `Procfile` in project root:
```
web: gunicorn app:app
```

**Step 6C-3:** Install Heroku CLI and deploy:
```bash
heroku login
heroku create hk-shipping-tracker
git push heroku main
```

---

### Option D: Deploy to AWS EC2 (VPS)

**Step 6D-1:** Launch an EC2 instance (Ubuntu 22.04)

**Step 6D-2:** SSH into your instance:
```bash
ssh -i your-key.pem ubuntu@your-instance-ip
```

**Step 6D-3:** Install dependencies:
```bash
sudo apt update
sudo apt install python3-pip python3-venv nginx
```

**Step 6D-4:** Clone your repository:
```bash
git clone https://github.com/YOUR_USERNAME/hk-shipping-tracker.git
cd hk-shipping-tracker
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Step 6D-5:** Configure Gunicorn and Nginx (see separate docs)

---

## Step 7: Set Up Database for Production

If using SQLite (hk_shipping.db), it will be created automatically. However:

**For cloud deployments:**
- SQLite may reset on Render/Railway free tier
- Consider migrating to PostgreSQL for persistence:
  ```bash
  pip install psycopg2-binary
  # Update DATABASE_FILE to use PostgreSQL connection string
  ```

---

## Step 8: Test Your Deployment

```bash
# Test locally first
python app.py

# Then visit: http://localhost:5000
# Check all pages and functionality
```

---

## Step 9: Set Up Custom Domain (Optional)

### For Render:
1. Go to your service settings
2. Click "Custom Domain"
3. Enter your domain
4. Add CNAME record to your DNS provider

### For Railway:
1. Go to "Settings" → "Domain"
2. Add your domain

---

## Step 10: Enable HTTPS

Most platforms (Render, Railway, Heroku) provide free SSL/TLS certificates automatically.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| App crashes on startup | Check logs: `heroku logs --tail` or Render dashboard logs |
| Database not found | Ensure `init_db()` runs on first deployment |
| Port 5000 not accessible | Use `os.environ.get('PORT', 5000)` in app.py |
| Static files not loading | Run `flask collectstatic` or ensure `static/` path is correct |

---

## Summary of Files to Create

Before deployment, ensure you have:
- ✅ `requirements.txt` - Python dependencies
- ✅ `.gitignore` - Excluded files
- ✅ `Procfile` - (for Heroku/Railway)
- ✅ `.env` - Environment variables (git-ignored)

