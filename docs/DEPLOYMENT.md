# 🚀 FastAPI Deployment Guide

Complete step-by-step guide to deploy your Pledge Receipt System to production.

## 📋 Prerequisites Checklist

- ✅ FastAPI application ready
- ✅ PostgreSQL database configured (Render.com)
- ✅ All dependencies in `requirements.txt`
- ✅ `.env` file with environment variables
- ✅ Git repository ready for deployment

---

## 🎯 Deployment Options

### Option 1: Render.com (⭐ RECOMMENDED)
- **Free tier available** with PostgreSQL
- **Easy deployment** from GitHub
- **Auto-scaling** and SSL included
- **Currently using** this for your database

### Option 2: Railway
- Modern deployment platform
- Good free tier
- Pay-as-you-go pricing

### Option 3: Heroku
- Classic choice but paid-only now
- Good documentation
- No free tier

### Option 4: AWS/DigitalOcean
- More complex setup
- Better for production at scale
- Higher control

---

## 🏆 Recommended: Deploy on Render.com

Your database is already on Render, so this is the **best choice for simplicity**.

### Step 1: Prepare Your Repository

```bash
# Ensure you have a .gitignore file
cat > .gitignore << 'EOF'
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
.env
.env.local
.DS_Store
.vscode/
.idea/
venv/
ENV/
env/
EOF

# Commit all changes
git add -A
git commit -m "Prepare for deployment"
git push
```

### Step 2: Create Render Web Service

1. **Go to Render.com** → https://render.com
2. **Sign in** with GitHub account
3. **Click "New +"** → Select **Web Service**
4. **Connect GitHub repository**
5. **Fill deployment form:**

   | Field | Value |
   |-------|-------|
   | **Name** | pledge-receipt-api (or your choice) |
   | **Region** | Oregon (same as database) |
   | **Branch** | main |
   | **Runtime** | Python 3.11 |
   | **Build Command** | `bash build.sh` |
   | **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port 8000` |

6. **Click "Create Web Service"**

### Step 3: Add Environment Variables

In Render dashboard, go to your Web Service → **Environment**

Add these variables:

```bash
DATABASE_URL=postgresql://pawnproledger_user:3rjb3ANcKd0Uaa2wPvAZ2wwUWYvvAXEc@dpg-d3s8q4q4d50c738kjof0-a.oregon-postgres.render.com/pawnproledger

SECRET_KEY=qB8rVNb6mKXtjswiwfAZuyI39IwANfh76h-T7QzG_D0

CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

DEBUG=False
```

> ⚠️ **IMPORTANT:** Change `SECRET_KEY` to a new secure value!

### Step 4: Generate New Secret Key

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the output and use it as your `SECRET_KEY` in Render environment.

### Step 5: Monitor Deployment

1. **Render Dashboard** → Your Web Service
2. **Logs tab** → Watch deployment progress
3. **Wait for "deployed successfully"** message
4. **Copy your URL** (e.g., `https://pledge-receipt-api.onrender.com`)

### Step 6: Test Your API

```bash
# Replace with your Render URL
curl https://pledge-receipt-api.onrender.com/docs

# Or open in browser:
https://pledge-receipt-api.onrender.com/docs
```

---

## 📝 Additional Configuration Files

### Procfile (if needed)

```bash
cat > Procfile << 'EOF'
web: uvicorn app.main:app --host 0.0.0.0 --port 8000
EOF

git add Procfile
git commit -m "Add Procfile for deployment"
git push
```

### runtime.txt (specify Python version)

```bash
cat > runtime.txt << 'EOF'
python-3.11.7
EOF

git add runtime.txt
git commit -m "Specify Python runtime version"
git push
```

---

## 🔒 Production Security Checklist

Before going live:

- [ ] Change `DEBUG=False` in environment
- [ ] Generate new `SECRET_KEY` (use command above)
- [ ] Set specific `CORS_ORIGINS` (not "*")
- [ ] Use HTTPS only (automatic on Render)
- [ ] Enable database backups (Render does this)
- [ ] Set up monitoring and alerts
- [ ] Review database credentials are correct
- [ ] Test all API endpoints
- [ ] Test authentication/authorization
- [ ] Verify database connection works

---

## 🧪 Testing Your Deployment

### Test 1: API Status
```bash
curl https://your-app.onrender.com/docs
```
Should show Swagger UI

### Test 2: Health Check
```bash
curl https://your-app.onrender.com/health
```
Should return 200 OK

### Test 3: API Endpoints
```bash
# Test authentication
curl -X POST https://your-app.onrender.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}'

# Test pledges
curl https://your-app.onrender.com/api/pledges
```

### Test 4: Database Connection
API should connect to database automatically.
Check Logs if there are connection errors.

---

## 🐛 Troubleshooting

### Problem: "Build failed"
- Check `requirements.txt` syntax
- Ensure all dependencies are listed
- Check Python version compatibility

### Problem: "Application failed to start"
- Check Start Command is correct
- Check environment variables are set
- Check for syntax errors in code

### Problem: "Database connection error"
- Verify `DATABASE_URL` is correct
- Check PostgreSQL is running
- Ensure firewall allows connections

### Problem: "Port already in use"
- Use `--port 8000` in start command
- Or set `PORT` environment variable

### Problem: "Module not found"
- Check `requirements.txt` has all imports
- Verify package names are correct
- Run `pip install -r requirements.txt` locally to test

### Problem: "Rust/Cargo compilation error" or "Read-only file system"
**Symptoms:**
- Error mentioning `maturin`, `cargo`, or `Rust toolchain`
- Message about "Read-only file system" during build
- Packages like `argon2-cffi` or `cryptography` failing to install

**Solution:**
This project includes a `build.sh` script that prevents these issues by forcing binary-only installation for Rust-based packages.

**Ensure your Render build command is set to:**
```
bash build.sh
```

**What the build script does:**
- Forces pip to use only pre-compiled binary wheels
- Prevents source compilation of Rust packages
- Avoids Cargo/maturin compilation in restricted environments

**If you're not using the build script, you can manually fix by:**
```bash
pip install --only-binary argon2-cffi,argon2-cffi-bindings,cryptography,passlib -r requirements.txt
```

---

## 📊 Monitoring

### View Logs on Render
1. **Dashboard** → Your Web Service
2. **Logs tab** → See real-time logs
3. **Metrics tab** → CPU, Memory, Bandwidth

### Set Up Alerts
1. **Settings** → Email Notifications
2. **Enable deployment alerts**
3. **Enable error alerts**

---

## 🔄 Continuous Deployment

Render automatically deploys when you push to main branch:

```bash
# Make changes locally
git add .
git commit -m "Update API endpoints"
git push origin main

# Render automatically:
# 1. Detects the push
# 2. Builds the application
# 3. Deploys to production
# 4. No downtime (blue-green deployment)
```

---

## 📱 Access Your API

After deployment:

| Resource | URL |
|----------|-----|
| **API Docs** | `https://your-app.onrender.com/docs` |
| **ReDoc** | `https://your-app.onrender.com/redoc` |
| **OpenAPI JSON** | `https://your-app.onrender.com/openapi.json` |
| **Health** | `https://your-app.onrender.com/health` |

---

## 💰 Costs

### Render.com Pricing
- **Web Service:** Free tier (limited), $7/month (production)
- **PostgreSQL:** Free tier (limited), $15/month (production)
- **Total:** ~$22/month for production

### Alternatives
- **Railway:** Similar pricing
- **AWS Free Tier:** Free for 1 year
- **DigitalOcean:** $5/month (basic)

---

## 🆚 Comparison: Deployment Platforms

| Feature | Render | Railway | Heroku | AWS |
|---------|--------|---------|--------|-----|
| **Free Tier** | Yes | Yes | No | Limited |
| **Ease** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| **GitHub Integration** | ✓ | ✓ | ✓ | ✓ |
| **Auto Deploy** | ✓ | ✓ | ✓ | Manual |
| **PostgreSQL** | ✓ | ✓ | ✓ | ✓ |
| **SSL/HTTPS** | ✓ | ✓ | ✓ | ✓ |
| **Docs** | Good | Good | Excellent | Complex |

---

## 📚 Next Steps After Deployment

1. **Configure Domain** (optional)
   - Add custom domain in Render settings
   - Update DNS records
   - Enable auto SSL

2. **Set Up Monitoring**
   - Enable uptime checks
   - Set up error alerts
   - Monitor database performance

3. **Backups**
   - Render backs up PostgreSQL daily
   - Export backups regularly
   - Test restore procedures

4. **CI/CD Pipeline** (optional)
   - Add GitHub Actions for testing
   - Automated tests before deploy
   - Staging environment

---

## ✅ Deployment Checklist

Before deploying:

- [ ] All tests pass locally
- [ ] `.env.example` has correct structure
- [ ] `.gitignore` excludes `.env`
- [ ] `requirements.txt` is up to date
- [ ] Git repository is clean
- [ ] All changes are committed
- [ ] Main branch is latest code
- [ ] Database migration scripts ready

After deploying:

- [ ] API is accessible
- [ ] Swagger docs work
- [ ] Database connection works
- [ ] Authentication works
- [ ] All endpoints tested
- [ ] Environment variables set
- [ ] Monitoring enabled
- [ ] Backups configured

---

## 🎓 Learning Resources

- **FastAPI Deployment:** https://fastapi.tiangolo.com/deployment/
- **Render Docs:** https://render.com/docs
- **PostgreSQL on Render:** https://render.com/docs/databases
- **Python Version Support:** https://www.python.org/

---

## 💬 Support

If you encounter issues:

1. **Check Render logs** for error messages
2. **Review environment variables** are set
3. **Test locally** with same configuration
4. **Check requirements.txt** for version conflicts
5. **Read error messages carefully** - they usually point to the issue

---

**Status:** Ready for Deployment ✅

Next: Follow the "Recommended: Deploy on Render.com" section step-by-step.
