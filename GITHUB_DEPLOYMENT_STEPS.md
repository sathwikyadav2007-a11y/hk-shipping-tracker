# 🚀 GitHub Deployment - Step by Step Guide

## STEP 1: Initialize Git Repository Locally
Run these commands in your project terminal:

```powershell
cd "c:\Users\sathw\OneDrive\Desktop\Transport Invoice & Payment Tracker-1"
git init
git add .
git commit -m "Initial commit: HK Shipping Flask application with deployment configs"
```

## STEP 2: Create GitHub Repository

1. Go to https://github.com/new
2. Login (or create account)
3. Fill in:
   - **Repository name:** `hk-shipping-tracker`
   - **Description:** Transport Invoice & Payment Tracker for HK Shipping
   - **Visibility:** Public (or Private if preferred)
4. Click **"Create repository"** (do NOT add README, .gitignore, or license)

## STEP 3: Connect Local Repo to GitHub

After repository is created, you'll see commands. Run these:

```powershell
git remote add origin https://github.com/YOUR_USERNAME/hk-shipping-tracker.git
git branch -M main
git push -u origin main
```

Replace `YOUR_USERNAME` with your actual GitHub username.

## STEP 4: Verify on GitHub

1. Go to your new repository: https://github.com/YOUR_USERNAME/hk-shipping-tracker
2. Verify all files are there:
   - app.py
   - requirements.txt ✅ (we created)
   - Procfile ✅ (we created)
   - .gitignore ✅ (we created)
   - README.md ✅ (we created)
   - templates/
   - static/

## STEP 5: Choose & Deploy to Free Platform

### Option A: RENDER.COM (Recommended - Easiest)

1. Go to https://render.com
2. Click **Sign up** (use GitHub to sign up)
3. Authorize GitHub access
4. Click **"New +"** → **"Web Service"**
5. Select your **hk-shipping-tracker** repository
6. Click **"Connect"**
7. Configure:
   - **Name:** hk-shipping-tracker (or any name)
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Instance Type:** Free
8. Click **"Create Web Service"**
9. Wait 2-3 minutes for deployment
10. Get your live URL: `https://hk-shipping-tracker.onrender.com`

### Option B: RAILWAY.APP (Very Simple)

1. Go to https://railway.app
2. Click **"Start Project"**
3. Select **"Deploy from GitHub repo"**
4. Authorize GitHub
5. Select **hk-shipping-tracker** repository
6. Railway auto-deploys in ~2-3 minutes
7. Your app is live at `https://your-domain.up.railway.app`

### Option C: HEROKU (Traditional)

1. Go to https://www.heroku.com/home
2. Sign up or log in
3. Install Heroku CLI: https://devcenter.heroku.com/articles/heroku-cli
4. Run:
   ```powershell
   heroku login
   heroku create hk-shipping-tracker
   git push heroku main
   heroku open
   ```

## STEP 6: Test Your Deployed App

Once deployed:
1. Click the live URL from your platform
2. Test the dashboard
3. Create sample bookings
4. Check if database initializes correctly

## STEP 7: Set Up Custom Domain (Optional)

### For Render:
1. Go to Service Settings
2. Click "Custom Domain"
3. Add your domain
4. Update DNS CNAME record

### For Railway:
1. Go to Settings → Domain
2. Add custom domain

## STEP 8: Enable Auto-Deployment from GitHub

Both Render and Railway automatically deploy when you push to GitHub:

```powershell
# Make a change locally
git add .
git commit -m "Update feature X"
git push origin main
# Your app automatically redeploys!
```

## TROUBLESHOOTING

| Issue | Solution |
|-------|----------|
| **App crashes** | Check deployment logs on Render/Railway dashboard |
| **Port errors** | We already fixed this in app.py (reads PORT env var) |
| **Static files 404** | Ensure correct paths in templates (they're correct) |
| **Database reset** | SQLite resets on free tier. Upgrade or use PostgreSQL |
| **Build fails** | Check that `requirements.txt` exists and is valid |

## NEXT STEPS AFTER DEPLOYMENT

1. **Monitor:** Check deployment logs regularly
2. **Backup:** Download database periodically
3. **Scale:** Upgrade to paid tier if needed
4. **Custom Domain:** Add your domain for professional look
5. **SSL/TLS:** Automatic HTTPS on all platforms

## Quick Reference

```powershell
# Update and redeploy
git add .
git commit -m "your message"
git push origin main

# Check git status
git status

# View deployment history
git log --oneline
```

---

**Choose ONE platform above (Render is easiest) and follow Steps 1-7.**
