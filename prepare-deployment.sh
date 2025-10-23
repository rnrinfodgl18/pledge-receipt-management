#!/bin/bash
# Deployment Preparation Script
# This script prepares the project for deployment to Render

set -e  # Exit on error

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                    DEPLOYMENT PREPARATION SCRIPT                            ║"
echo "║                  Preparing FastAPI for Production Deployment                ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Step 1: Check if Git is initialized
echo "📋 Step 1: Checking Git Repository..."
if [ -d ".git" ]; then
    echo "✅ Git repository found"
else
    echo "❌ Git repository not found. Initializing..."
    git init
    echo "✅ Git repository initialized"
fi
echo ""

# Step 2: Check .gitignore
echo "📋 Step 2: Creating/Updating .gitignore..."
if [ -f ".gitignore" ]; then
    echo "✅ .gitignore already exists"
else
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
.vscode/settings.json
.idea/
venv/
ENV/
env/
*.log
.pytest_cache/
.coverage
htmlcov/
dist/
build/
*.egg-info/
.mypy_cache/
.dmypy.json
dmypy.json
EOF
    echo "✅ .gitignore created"
fi
echo ""

# Step 3: Check Procfile
echo "📋 Step 3: Creating Procfile..."
if [ -f "Procfile" ]; then
    echo "✅ Procfile already exists"
else
    cat > Procfile << 'EOF'
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
EOF
    echo "✅ Procfile created"
fi
echo ""

# Step 4: Check runtime.txt
echo "📋 Step 4: Creating runtime.txt..."
if [ -f "runtime.txt" ]; then
    echo "✅ runtime.txt already exists"
else
    cat > runtime.txt << 'EOF'
python-3.11.7
EOF
    echo "✅ runtime.txt created"
fi
echo ""

# Step 5: Verify requirements.txt
echo "📋 Step 5: Verifying requirements.txt..."
if [ -f "requirements.txt" ]; then
    echo "✅ requirements.txt found"
    echo "   Dependencies:"
    head -5 requirements.txt | sed 's/^/   - /'
    echo "   ..."
else
    echo "❌ requirements.txt not found!"
    exit 1
fi
echo ""

# Step 6: Verify .env.example
echo "📋 Step 6: Verifying .env.example..."
if [ -f ".env.example" ]; then
    echo "✅ .env.example found"
else
    echo "⚠️  .env.example not found. Creating template..."
    cat > .env.example << 'EOF'
# Environment Configuration for Deployment

# PostgreSQL Database Configuration
DATABASE_URL=postgresql://user:password@host:5432/database

# JWT Secret Key (Generate new for production!)
# python -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY=your_secret_key_here

# CORS Origins - Comma-separated list
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Debug Mode (False in production)
DEBUG=False
EOF
    echo "✅ .env.example created"
fi
echo ""

# Step 7: Check .env file
echo "📋 Step 7: Checking .env file..."
if [ -f ".env" ]; then
    echo "✅ .env file exists (will not be committed)"
else
    echo "⚠️  .env file not found. Remember to create it locally."
    echo "   Copy from .env.example: cp .env.example .env"
fi
echo ""

# Step 8: Git Status
echo "📋 Step 8: Git Status..."
echo "   Current branch:"
git branch --show-current 2>/dev/null || echo "   (No branch info)"
echo "   Staged changes:"
git status --short 2>/dev/null || echo "   (No git info)"
echo ""

# Step 9: Summary
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                       ✅ PREPARATION COMPLETE                               ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "📝 DEPLOYMENT CHECKLIST:"
echo ""
echo "✅ Files prepared:"
echo "   - .gitignore"
echo "   - Procfile"
echo "   - runtime.txt"
echo "   - requirements.txt"
echo "   - .env.example"
echo ""
echo "📋 NEXT STEPS:"
echo ""
echo "1. Update your local .env file:"
echo "   cp .env.example .env"
echo "   # Edit .env with your production values"
echo ""
echo "2. Commit changes to Git:"
echo "   git add -A"
echo "   git commit -m 'Prepare for production deployment'"
echo "   git push origin main"
echo ""
echo "3. Deploy on Render:"
echo "   a) Go to https://render.com"
echo "   b) Create new Web Service"
echo "   c) Connect your GitHub repository"
echo "   d) Set environment variables"
echo "   e) Deploy!"
echo ""
echo "4. After deployment:"
echo "   - Test API at https://your-app.onrender.com/docs"
echo "   - Check logs for any errors"
echo "   - Monitor database connection"
echo ""
echo "📚 For detailed instructions, see: /docs/DEPLOYMENT.md"
echo ""
echo "🚀 Ready to deploy!"
