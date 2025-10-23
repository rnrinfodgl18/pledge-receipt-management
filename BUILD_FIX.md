# Build Script Fix for Rust Compilation Issues

## Problem

When deploying to cloud platforms like Render, Railway, or Heroku, you may encounter errors like:

```
error: failed to create directory `/usr/local/cargo/registry/cache/index.crates.io-...`
Caused by: Read-only file system (os error 30)
💥 maturin failed
```

This happens when Python packages with Rust dependencies (like `argon2-cffi` or `cryptography`) try to compile from source in a restricted build environment.

## Solution

This repository includes a `build.sh` script that solves this issue by:

1. **Forcing binary-only installation** for packages with Rust dependencies
2. **Preventing source compilation** that requires Cargo/Rust toolchain
3. **Ensuring pre-built wheels are used** instead of building from source

## Usage

### On Render.com

Set your **Build Command** to:
```bash
bash build.sh
```

### On Railway

Add to your `railway.toml`:
```toml
[build]
builder = "nixpacks"
buildCommand = "bash build.sh"
```

### On Heroku

Update your `Procfile` or set the build command in Heroku settings:
```bash
web: bash build.sh && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## Alternative: Using render.yaml

This repository includes a `render.yaml` file that automatically configures the build:

```yaml
services:
  - type: web
    name: pledge-receipt-api
    runtime: python
    buildCommand: bash build.sh
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Just commit this file to your repository and Render will use it automatically.

## Manual Fix

If you prefer not to use the build script, you can manually specify binary-only installation:

```bash
pip install \
  --only-binary argon2-cffi \
  --only-binary argon2-cffi-bindings \
  --only-binary cryptography \
  --only-binary passlib \
  -r requirements.txt
```

## Affected Packages

The following packages may require Rust compilation if installed from source:

- `argon2-cffi` (>= 23.1.0) - Password hashing
- `argon2-cffi-bindings` - Low-level bindings for argon2-cffi
- `cryptography` (>= 41.0.0) - Cryptographic recipes
- `passlib[argon2]` - Password hashing library

## Why This Happens

Modern versions of these packages use Rust for performance-critical operations. When binary wheels aren't available for your platform/Python version combination, pip tries to build from source, which requires:

1. Rust toolchain (`rustc`, `cargo`)
2. Write access to the Cargo registry
3. C/C++ compilers

Cloud platforms often have read-only file systems or don't include the full Rust toolchain in their build environments, causing compilation to fail.

## Benefits of Binary Wheels

Using pre-built binary wheels:
- ✅ Faster builds (no compilation needed)
- ✅ Works in restricted environments
- ✅ Consistent builds across platforms
- ✅ Smaller attack surface (no build tools needed)

## Verification

To verify the build script works correctly:

1. **Test locally:**
   ```bash
   python3 -m venv test_env
   source test_env/bin/activate
   bash build.sh
   ```

2. **Check for Rust/Cargo errors** - there should be none

3. **Verify packages installed:**
   ```bash
   pip list | grep -E "argon2|cryptography|passlib"
   ```

## Related Issues

- [argon2-cffi #159](https://github.com/hynek/argon2-cffi/issues/159) - Build issues on various platforms
- [cryptography docs](https://cryptography.io/en/latest/installation/) - Installation requirements

## Support

If you still encounter build issues after using this script:

1. Check your Python version matches `runtime.txt` (3.11.7)
2. Ensure the build command is correctly set to `bash build.sh`
3. Check the build logs for specific error messages
4. Verify all packages in `requirements.txt` have binary wheels available for your platform

---

**Last Updated:** October 2025  
**Status:** ✅ Tested and Working
