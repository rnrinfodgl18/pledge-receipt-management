#!/bin/bash
# GitHub Repository Setup Script
# This script helps you push code to GitHub

set -e

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                   GITHUB REPOSITORY SETUP SCRIPT                            ║"
echo "║              Push Your FastAPI Application to GitHub                        ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Step 1: Check if Git is initialized
echo "📋 Step 1: Checking Git Repository..."
if [ -d ".git" ]; then
    echo "✅ Git repository is initialized"
else
    echo "❌ Git repository not found!"
    echo "   Initializing Git..."
    git init
    echo "✅ Git repository initialized"
fi
echo ""

# Step 2: Configure Git user
echo "📋 Step 2: Configure Git User..."
echo ""
echo "📝 Enter your GitHub username:"
read -r GITHUB_USER

echo "📝 Enter your email address:"
read -r EMAIL

git config --global user.name "$GITHUB_USER"
git config --global user.email "$EMAIL"
echo "✅ Git user configured: $GITHUB_USER <$EMAIL>"
echo ""

# Step 3: Display repository instructions
echo "📋 Step 3: Create Repository on GitHub..."
echo ""
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                    CREATE REPOSITORY ON GITHUB                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "1. Go to: https://github.com/new"
echo "2. Fill in the form:"
echo ""
echo "   Repository name: pledge-receipt-system"
echo "   Description: FastAPI application for pledge receipt management"
echo "   Visibility: Public or Private (your choice)"
echo "   Initialize: ✗ (don't check any boxes)"
echo ""
echo "3. Click 'Create repository'"
echo "4. Copy the HTTPS URL (e.g., https://github.com/yourusername/pledge-receipt-system.git)"
echo ""
read -p "👉 Press Enter after creating repository and copying URL..."
echo ""

echo "📝 Paste your GitHub repository URL:"
read -r REPO_URL

# Validate URL
if [[ ! $REPO_URL =~ ^https://github.com/ ]]; then
    echo "❌ Invalid GitHub URL format!"
    echo "   Expected format: https://github.com/yourusername/repo-name.git"
    exit 1
fi

echo "✅ Repository URL: $REPO_URL"
echo ""

# Step 4: Add remote
echo "📋 Step 4: Connecting Local Repository to GitHub..."
if git remote | grep -q origin; then
    echo "⚠️  Remote 'origin' already exists. Removing..."
    git remote remove origin
fi

git remote add origin "$REPO_URL"
echo "✅ Remote 'origin' added"

# Verify
git remote -v
echo ""

# Step 5: Check Git status
echo "📋 Step 5: Checking Files to Commit..."
echo ""
echo "📂 Untracked files that will be committed:"
git status --short | head -20
echo ""

# Step 6: Stage all files
echo "📋 Step 6: Staging All Files..."
git add -A
echo "✅ All files staged"
echo ""

# Step 7: Create commit
echo "📋 Step 7: Creating Initial Commit..."
git commit -m "Initial commit: Pledge Receipt System ready for deployment

Features:
- Pledge receipt models and schemas
- 8 API endpoints for receipt management
- Automatic pledge status updates on full payment
- Automatic COA entry reversals on receipt void
- JWT authentication and authorization
- Complete API documentation

Files included:
- FastAPI application with PostgreSQL integration
- Database models and Pydantic schemas
- Utility functions for automatic features
- Comprehensive documentation
- Deployment configuration (Procfile, runtime.txt)
- .env template for environment variables

Ready to deploy to Render.com or similar platforms."

echo "✅ Initial commit created"
echo ""

# Step 8: Set main branch
echo "📋 Step 8: Setting Main Branch..."
git branch -M main
echo "✅ Main branch configured"
echo ""

# Step 9: Push to GitHub
echo "📋 Step 9: Pushing Code to GitHub..."
echo ""
echo "⚠️  You may be prompted for authentication:"
echo "   - Use your GitHub username"
echo "   - For password, use a Personal Access Token"
echo "   - Generate token at: https://github.com/settings/tokens"
echo ""
read -p "👉 Press Enter to continue with push..."
echo ""

git push -u origin main

echo ""
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                       ✅ PUSH COMPLETE!                                     ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "🎉 Your code is now on GitHub!"
echo ""
echo "📊 Repository Details:"
echo "   URL: $REPO_URL"
echo "   Branch: main"
echo "   Commit: Initial commit"
echo ""
echo "🔗 View your repository:"
echo "   $REPO_URL"
echo ""
echo "📚 Next Steps:"
echo ""
echo "1. Deploy to Render:"
echo "   - Go to https://render.com"
echo "   - Create new Web Service"
echo "   - Select your GitHub repository"
echo "   - Deploy!"
echo ""
echo "2. For future updates:"
echo "   git add ."
echo "   git commit -m 'Your message'"
echo "   git push origin main"
echo ""
echo "📖 For detailed instructions, see: GITHUB_SETUP.md"
echo ""
echo "✨ Your project is now ready for production deployment!"
