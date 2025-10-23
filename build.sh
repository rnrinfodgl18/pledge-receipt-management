#!/bin/bash
# Build script for Render deployment
# This script ensures packages are installed using only binary wheels
# to avoid Rust/C++ compilation issues in the build environment

set -e  # Exit on error

echo "🔧 Starting build process..."

# Upgrade pip to latest version
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install dependencies using only binary wheels for packages that require Rust
# This prevents compilation issues with argon2-cffi, cryptography, etc.
echo "📦 Installing dependencies (binary-only mode for Rust packages)..."
pip install \
  --only-binary argon2-cffi \
  --only-binary argon2-cffi-bindings \
  --only-binary cryptography \
  --only-binary passlib \
  -r requirements.txt

echo "✅ Build completed successfully!"
