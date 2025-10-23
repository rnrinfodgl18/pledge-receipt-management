# 🚀 Complete Deployment Workflow: GitHub → Render

Complete guide to push code to GitHub and deploy to Render in ~15 minutes.

---

## 📋 Overview

```
Your Local Machine
        ↓
   Push to GitHub
        ↓
  Render sees push
        ↓
Render builds & deploys
        ↓
✅ Live on Internet!
```

---

## 🎯 Part 1: Push Code to GitHub (5 minutes)

### Option A: Automated Script (Easiest)

```bash
chmod +x push-to-github.sh
./push-to-github.sh
```

The script will:
1. Ask for your GitHub username and email
2. Guide you to create repository on GitHub.com
3. Connect local repo to GitHub
4. Stage and commit all files
5. Push to GitHub

### Option B: Manual Steps

#### 1. Create Repository on GitHub

1. Go to: https://github.com/new
2. Fill form:
   - **Repository name:** `pledge-receipt-system`
   - **Description:** FastAPI application for pledge receipt management
   - **Visibility:** Public (for deployment) or Private
   - **Don't initialize anything** (we have files already)
3. Click **"Create repository"**
4. Copy the URL (e.g., `https://github.com/yourusername/pledge-receipt-system.git`)

#### 2. Configure Git

```bash
cd /workspaces/codespaces-blank

# Set your GitHub credentials
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Add GitHub remote
git remote add origin https://github.com/yourusername/pledge-receipt-system.git

# Verify connection
git remote -v
```

#### 3. Commit Code

```bash
git add -A
git commit -m "Initial commit: Pledge Receipt System ready for deployment"
```

#### 4. Push to GitHub

```bash
git branch -M main
git push -u origin main
```

**When prompted for password:** Use a GitHub Personal Access Token instead of your password.

Generate token at: https://github.com/settings/tokens
- Scope needed: `repo`

---

## ✅ Verify on GitHub

After pushing:

1. Open your repository: `https://github.com/yourusername/pledge-receipt-system`
2. Verify all files are there:
   - ✅ `app/` folder
   - ✅ `docs/` folder
   - ✅ `Procfile`
   - ✅ `requirements.txt`
   - ✅ `README.md`

---

## 🚀 Part 2: Deploy to Render (10 minutes)

### Step 1: Go to Render

1. Visit: https://render.com
2. Click **"Sign up"** or **"Sign in"** with GitHub
3. Authorize Render to access your GitHub account

### Step 2: Create Web Service

1. Click **"New +"** → **"Web Service"**
2. **Authorize GitHub** (if prompted)
3. **Select your repository:** `pledge-receipt-system`
4. Click **"Connect"**

### Step 3: Configure Service

Fill the form with:

| Field | Value |
|-------|-------|
| **Name** | `pledge-receipt-api` |
| **Region** | `Oregon` (same as your database) |
| **Branch** | `main` |
| **Runtime** | `Python 3.11` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port 8000` |

### Step 4: Add Environment Variables

Click **"Environment"** tab and add:

```
DATABASE_URL=postgresql://pawnproledger_user:3rjb3ANcKd0Uaa2wPvAZ2wwUWYvvAXEc@dpg-d3s8q4q4d50c738kjof0-a.oregon-postgres.render.com/pawnproledger

SECRET_KEY=<generate new key>

CORS_ORIGINS=https://yourdomain.com

DEBUG=False
```

**Generate new SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Step 5: Deploy

1. Click **"Create Web Service"**
2. Wait 2-3 minutes for deployment
3. Watch the logs in Render dashboard
4. When status is "live" ✅ → You're deployed!

### Step 6: Get Your URL

In Render dashboard:
- Your service URL will be shown (e.g., `https://pledge-receipt-api.onrender.com`)
- Save this URL!

---

## 🧪 Test Your Deployment

### Test 1: Access API Documentation

```bash
curl https://your-app.onrender.com/docs
```

Or open in browser: `https://your-app.onrender.com/docs`

Should show Swagger UI with all API endpoints.

### Test 2: Test an Endpoint

```bash
curl https://your-app.onrender.com/api/pledges
```

Should return list of pledges (or empty list if no data).

### Test 3: Check Logs

In Render Dashboard:
- **Logs** tab → See deployment and runtime logs
- **Metrics** tab → CPU, Memory, Bandwidth usage

---

## 🔄 Update Your Application

After deploying, whenever you make changes:

```bash
# 1. Make changes to files
# 2. Stage changes
git add .

# 3. Commit with descriptive message
git commit -m "Add new feature: XYZ"

# 4. Push to GitHub
git push origin main

# 5. Render automatically detects the push and:
#    - Pulls latest code
#    - Rebuilds application
#    - Deploys new version
#    - Zero downtime!
```

You can watch the deployment in Render dashboard **Deploys** tab.

---

## 📊 Complete Workflow Summary

### Before Deployment
```
Local Development
└─ git add .
└─ git commit -m "message"
```

### GitHub Push
```
git push origin main
└─ Code uploaded to GitHub
└─ GitHub shows repository with all files
```

### Render Deployment
```
Render detects push (webhook)
└─ Pull latest code from GitHub
└─ Install dependencies (requirements.txt)
└─ Run start command (uvicorn)
└─ Database connections automatically
└─ API live on https://your-app.onrender.com
```

### After Deployment
```
User accesses API
└─ https://your-app.onrender.com/docs
└─ Can call all 8 receipt endpoints
└─ Can call all pledge endpoints
└─ Can authenticate and use API
```

---

## 🔐 Security Checklist

Before going live:

- [ ] GitHub repository is private (optional but recommended)
- [ ] `.env` file is NOT in Git (check `.gitignore`)
- [ ] `DEBUG=False` in Render environment
- [ ] New `SECRET_KEY` generated and set
- [ ] `CORS_ORIGINS` is set to your domain (not "*")
- [ ] Database URL is correct
- [ ] API endpoints are tested
- [ ] Authentication is working
- [ ] Logs show no errors

---

## 🆘 Troubleshooting

### GitHub Push Issues

**Problem:** "fatal: not a git repository"
```bash
git init
git add .
git commit -m "Initial commit"
git push origin main
```

**Problem:** "Authentication failed"
- Use Personal Access Token instead of password
- Generate at: https://github.com/settings/tokens

**Problem:** "remote origin already exists"
```bash
git remote remove origin
git remote add origin https://github.com/yourusername/repo.git
```

### Render Deployment Issues

**Problem:** "Build failed"
- Check logs in Render dashboard
- Verify `requirements.txt` syntax
- Check all dependencies are listed

**Problem:** "Application crashed"
- Check environment variables in Render
- Check start command is correct
- View logs for error messages

**Problem:** "Database connection error"
- Verify DATABASE_URL is correct
- Check PostgreSQL is running
- Verify firewall allows connections

**Problem:** "Port already in use"
- Use `--port 8000` in start command
- Or set PORT environment variable

---

## 💡 Useful Commands

```bash
# Check Git status
git status

# View commits
git log --oneline -5

# Check remotes
git remote -v

# Pull latest from GitHub
git pull origin main

# Create new branch
git checkout -b feature-name

# View Render logs (after deployment)
# Go to: https://dashboard.render.com
# Select your service → Logs tab
```

---

## 📚 Documentation Structure

After setup, you have:

```
/workspaces/codespaces-blank/
├── GitHub Setup & Deployment
│   ├── GITHUB_SETUP.md (this file)
│   ├── DEPLOYMENT_READY.md
│   └── push-to-github.sh
│
├── Deployment Configuration
│   ├── Procfile (how to run)
│   ├── runtime.txt (Python version)
│   ├── requirements.txt (dependencies)
│   └── .env.example (config template)
│
├── Code Documentation
│   └── docs/
│       ├── DEPLOYMENT.md (full deployment guide)
│       ├── API_REFERENCE.md (all endpoints)
│       ├── README.md (overview)
│       └── 7 more files
│
└── Application Code
    └── app/
        ├── main.py (entry point)
        ├── models.py (database models)
        ├── routes/ (API endpoints)
        └── ...
```

---

## ✅ Step-by-Step Checklist

**Local Setup:**
- [ ] Code committed to local Git
- [ ] `.gitignore` properly configured
- [ ] No sensitive files in commits

**GitHub:**
- [ ] Repository created on GitHub
- [ ] Code pushed to GitHub
- [ ] All files visible on GitHub.com

**Render:**
- [ ] Render account created
- [ ] Web Service created from GitHub repo
- [ ] Environment variables set
- [ ] Application deployed successfully
- [ ] Logs show "live"

**Testing:**
- [ ] API documentation loads
- [ ] Endpoints respond correctly
- [ ] Database connection works
- [ ] Authentication works
- [ ] No errors in logs

---

## 🎯 Next Actions

**Immediate:**
1. ✅ Push code to GitHub
2. ✅ Deploy to Render
3. ✅ Test API

**Today:**
1. ✅ Verify all endpoints work
2. ✅ Set up custom domain (optional)
3. ✅ Monitor logs for errors

**This Week:**
1. ✅ Set up monitoring/alerts
2. ✅ Create CI/CD pipeline (optional)
3. ✅ Configure automatic backups

---

## 📖 Quick Reference Links

- **GitHub:** https://github.com
- **Render:** https://render.com
- **GitHub Docs:** https://docs.github.com
- **Render Docs:** https://render.com/docs
- **FastAPI Docs:** https://fastapi.tiangolo.com
- **Personal Access Token:** https://github.com/settings/tokens

---

## 🎓 Learning Path

1. **Understand GitHub:**
   - What is version control?
   - Why use GitHub?
   - How to push code?

2. **Understand Deployment:**
   - What is deployment?
   - How does Render work?
   - Auto-deployment from GitHub?

3. **Understand CI/CD (Optional):**
   - Automated testing
   - Automated deployment
   - GitHub Actions

4. **Advanced (Optional):**
   - Custom domain
   - SSL certificates
   - Database backups
   - Monitoring & alerts

---

## 🚀 You're Ready!

Your application is configured, documented, and ready to deploy.

**Timeline:**
- GitHub setup: 5 minutes
- Render deployment: 10 minutes
- Testing: 5 minutes
- **Total: ~20 minutes to go live!**

**Let's deploy! 🎉**

---

**Last Updated:** October 23, 2025  
**Status:** ✅ Ready for Production
