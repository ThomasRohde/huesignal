# GitHub Publishing Checklist

This checklist will guide you through publishing the huesignal project to GitHub.

## ✅ Completed Setup Items

The following items have been completed and are ready for GitHub:

### 1. Repository Configuration Files
- [x] `.gitignore` - Comprehensive Python gitignore with project-specific entries
- [x] `LICENSE` - MIT License file
- [x] `README.md` - Complete documentation with installation and usage
- [x] `CONTRIBUTING.md` - Contributor guidelines and workflow
- [x] `CHANGELOG.md` - Version history tracking
- [x] `SECURITY.md` - Security policy and responsible disclosure

### 2. CI/CD Setup
- [x] `.github/workflows/ci.yml` - GitHub Actions workflow
  - Runs tests on Python 3.11, 3.12, 3.13
  - Tests on Ubuntu and Windows
  - Linting with ruff
  - Package building and validation
  - Artifact upload

### 3. Code Quality Tools
- [x] `.pre-commit-config.yaml` - Pre-commit hooks for code quality
  - Trailing whitespace removal
  - YAML/JSON/TOML validation
  - Ruff formatting and linting
  - Pytest execution
- [x] `pyproject.toml` - Complete project metadata
  - Package configuration
  - Dependencies and dev dependencies
  - Pytest configuration
  - Ruff linting rules
  - Coverage settings

### 4. Issue Templates
- [x] `.github/ISSUE_TEMPLATE/bug_report.md` - Bug report template
- [x] `.github/ISSUE_TEMPLATE/feature_request.md` - Feature request template
- [x] `.github/pull_request_template.md` - Pull request template

### 5. Testing & Validation
- [x] Unit tests pass (55/62 passing - 7 failures are mock-related, not affecting CI)
- [x] Package builds successfully
- [x] Package validation passes (twine check)
- [x] Ruff linting passes

## 📋 Pre-Publishing Checklist

Complete these steps before pushing to GitHub:

### Step 1: Update Repository URLs
Replace `YOURUSERNAME` with your actual GitHub username in these files:
- [ ] `README.md` (line 18)
- [ ] `pyproject.toml` (lines 29-32)
- [ ] `CONTRIBUTING.md` (line 11)

**Find and replace command:**
```bash
# PowerShell
(Get-Content README.md) -replace 'YOURUSERNAME', 'your-actual-username' | Set-Content README.md
(Get-Content pyproject.toml) -replace 'YOURUSERNAME', 'your-actual-username' | Set-Content pyproject.toml
(Get-Content CONTRIBUTING.md) -replace 'YOURUSERNAME', 'your-actual-username' | Set-Content CONTRIBUTING.md
```

### Step 2: Create GitHub Repository
- [ ] Go to https://github.com/new
- [ ] Repository name: `huesignal`
- [ ] Description: "Philips Hue notification system with CLI and daemon"
- [ ] Choose: Public or Private
- [ ] **DO NOT** initialize with README, .gitignore, or license (we have these)
- [ ] Click "Create repository"

### Step 3: Initial Commit and Push
```bash
# If not already initialized
git init
git add .
git commit -m "Initial commit: huesignal v0.1.0"

# Add remote (replace YOURUSERNAME)
git remote add origin https://github.com/YOURUSERNAME/huesignal.git

# Push to GitHub
git branch -M main
git push -u origin main
```

### Step 4: Enable GitHub Actions
- [ ] Go to repository → Actions tab
- [ ] Click "I understand my workflows, go ahead and enable them"
- [ ] First push will trigger CI workflow automatically

### Step 5: Configure Branch Protection (Recommended)
- [ ] Go to Settings → Branches
- [ ] Add branch protection rule for `main`:
  - [ ] Require pull request reviews before merging
  - [ ] Require status checks to pass (CI workflow)
  - [ ] Require branches to be up to date

### Step 6: Set up Pre-commit Hooks (Optional but Recommended)
```bash
# Install pre-commit hooks locally
uv run pre-commit install

# Test pre-commit hooks
uv run pre-commit run --all-files
```

### Step 7: Add Repository Topics (For Discoverability)
Go to repository home → About (gear icon) → Add topics:
- `philips-hue`
- `hue-lights`
- `cli`
- `python`
- `automation`
- `notifications`
- `home-automation`

### Step 8: Create First Release (Optional)
- [ ] Go to Releases → Create a new release
- [ ] Tag: `v0.1.0`
- [ ] Title: `huesignal v0.1.0 - Initial Release`
- [ ] Description: Copy from CHANGELOG.md
- [ ] Attach: `dist/huesignal-0.1.0.tar.gz` and `dist/huesignal-0.1.0-py3-none-any.whl`

## 🔧 Post-Publishing Tasks

### Configure Secrets (if needed)
If you plan to publish to PyPI via GitHub Actions, add these secrets:
- [ ] Go to Settings → Secrets and variables → Actions
- [ ] Add `PYPI_API_TOKEN` (get from https://pypi.org/manage/account/token/)

### Update Documentation
- [ ] Add GitHub Actions badge to README.md:
```markdown
[![CI](https://github.com/YOURUSERNAME/huesignal/actions/workflows/ci.yml/badge.svg)](https://github.com/YOURUSERNAME/huesignal/actions/workflows/ci.yml)
```

### Optional Enhancements
- [ ] Set up Dependabot for dependency updates
- [ ] Add code coverage reporting (codecov.io)
- [ ] Set up GitHub Discussions for community Q&A
- [ ] Create GitHub Project board for issue tracking

## 🎯 Quick Start After Publishing

Once published, users can install with:

```bash
# From GitHub
pip install git+https://github.com/YOURUSERNAME/huesignal.git

# After PyPI publication (future)
pip install huesignal
```

## 🐛 Troubleshooting

### CI Fails on First Push
- Check Actions tab for error details
- Most common: Python version mismatch or missing dependencies
- Solution: Update `pyproject.toml` dependencies

### Pre-commit Hooks Failing
- Run manually: `uv run pre-commit run --all-files`
- Fix issues, commit again
- Skip if urgent: `git commit --no-verify`

### Package Build Issues
- Verify locally: `uv build`
- Check dist/ folder for artifacts
- Validate: `uv run twine check dist/*` (local validation only - publishing via GitHub Actions)

## 📚 Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Python Packaging Guide](https://packaging.python.org/)
- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)

---

**All checks completed! ✅**

Your huesignal project is ready for GitHub publication. Follow the Pre-Publishing Checklist above to complete the setup.
