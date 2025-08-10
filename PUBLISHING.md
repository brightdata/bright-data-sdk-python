# Publishing Guide

## GitHub Setup

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Initial release v1.0.0"
   git tag v1.0.0
   git push origin main --tags
   ```

2. **Install from GitHub:**
   ```bash
   # Install directly from GitHub
   pip install git+https://github.com/yourusername/bright-data-sdk-python.git
   
   # Or clone and install
   git clone https://github.com/yourusername/bright-data-sdk-python.git
   cd bright-data-sdk-python
   pip install .
   ```

## PyPI Publishing

### Test PyPI First (Recommended)

1. **Register at Test PyPI:** https://test.pypi.org/account/register/
2. **Create API Token:** Account settings → API tokens
3. **Configure credentials:**
   ```bash
   pip install twine
   ```
4. **Upload to Test PyPI:**
   ```bash
   twine upload --repository testpypi dist/*
   ```
5. **Test installation:**
   ```bash
   pip install --index-url https://test.pypi.org/simple/ brightdata
   ```

### Production PyPI

1. **Register at PyPI:** https://pypi.org/account/register/
2. **Create API Token:** Account settings → API tokens
3. **Upload to PyPI:**
   ```bash
   twine upload dist/*
   ```
4. **Verify installation:**
   ```bash
   pip install brightdata
   ```

## Automated Publishing (GitHub Actions)

The project includes GitHub Actions workflows:
- `test.yml` - Runs tests on push/PR
- `publish.yml` - Automatically publishes to PyPI on release

### Setup Secrets:
1. Go to GitHub repository → Settings → Secrets → Actions
2. Add secret: `PYPI_API_TOKEN` with your PyPI API token

### Create Release:
1. Create a new release on GitHub
2. Use tag format: `v1.0.0`
3. GitHub Actions will automatically build and publish

## Manual Build Commands

```bash
# Clean build
rm -rf dist/ build/ *.egg-info/

# Build distributions
python setup.py sdist bdist_wheel

# Check distributions
twine check dist/*

# Upload to PyPI
twine upload dist/*
```

## Version Updates

When releasing new versions:
1. Update version in `pyproject.toml` and `brightdata/__init__.py`
2. Update `CHANGELOG.md`
3. Create git tag with `v` prefix
4. Push tags to trigger automated publishing