# GitHub Setup Quick Reference

## 🚀 Quick Publish Commands

```bash
# 1. Update usernames (do this first!)
# Replace YOURUSERNAME with your GitHub username in:
#   - README.md
#   - pyproject.toml  
#   - CONTRIBUTING.md

# 2. Create GitHub repo at https://github.com/new
#    Name: huesignal
#    Don't initialize with any files

# 3. Push to GitHub
git remote add origin https://github.com/YOURUSERNAME/huesignal.git
git branch -M main
git add .
git commit -m "Initial commit: Ready for GitHub"
git push -u origin main

# 4. Enable GitHub Actions
# Visit: https://github.com/YOURUSERNAME/huesignal/actions
```

## ✅ Pre-Push Checklist

- [ ] Replaced all `YOURUSERNAME` placeholders
- [ ] Created GitHub repository
- [ ] Committed all changes locally
- [ ] Ready to push

## 🔧 Local Verification Commands

```bash
# Run tests
uv run pytest tests/ --ignore=tests/integration/

# Check linting
uv run ruff check src/ tests/

# Build package
uv build

# Validate package
uv run twine check dist/*

# Install pre-commit hooks
uv run pre-commit install

# Test pre-commit hooks
uv run pre-commit run --all-files
```

## 📁 New Files Added

### GitHub Configuration
- `.github/workflows/ci.yml` - CI/CD pipeline
- `.github/ISSUE_TEMPLATE/bug_report.md` - Bug report template
- `.github/ISSUE_TEMPLATE/feature_request.md` - Feature request template
- `.github/pull_request_template.md` - PR template

### Quality Control
- `.pre-commit-config.yaml` - Pre-commit hooks
- Enhanced `pyproject.toml` - Project metadata & tool config

### Documentation
- `LICENSE` - MIT License
- `CONTRIBUTING.md` - Contribution guidelines
- `CHANGELOG.md` - Version history
- `SECURITY.md` - Security policy
- `GITHUB_CHECKLIST.md` - Detailed publishing steps
- `GITHUB_PREP_SUMMARY.md` - Complete summary report

### Build Artifacts (gitignored)
- `dist/` - Built packages

## 🎯 CI Workflow Matrix

The CI runs on:
- **Python**: 3.11, 3.12, 3.13
- **OS**: Ubuntu Latest, Windows Latest
- **Jobs**: Test → Lint → Build

## 🔑 Key Features

✅ **Automated Testing**: Every PR is tested  
✅ **Code Quality**: Ruff enforces style  
✅ **Package Validation**: Twine checks packages  
✅ **Cross-Platform**: Tests on Windows & Linux  
✅ **Multi-Version**: Tests Python 3.11-3.13  
✅ **Pre-commit Hooks**: Local quality checks  

## 📊 CI Status

After first push, add this badge to README.md:

```markdown
[![CI](https://github.com/YOURUSERNAME/huesignal/actions/workflows/ci.yml/badge.svg)](https://github.com/YOURUSERNAME/huesignal/actions/workflows/ci.yml)
```

## 🐛 If CI Fails

1. Check the Actions tab
2. Review error logs
3. Fix locally and push again
4. Common issues:
   - Missing dependencies → Update pyproject.toml
   - Test failures → Check test logs
   - Linting errors → Run `ruff check --fix`

## 💡 Tips

- Use pre-commit hooks to catch issues early
- Test locally before pushing
- Write clear commit messages
- Keep PRs focused and small
- Update CHANGELOG.md for releases

## 📚 Documentation URLs

- GitHub Actions: https://docs.github.com/actions
- Pre-commit: https://pre-commit.com
- Ruff: https://github.com/astral-sh/ruff
- pytest: https://docs.pytest.org
- uv: https://github.com/astral-sh/uv

---

**Ready to publish!** 🎉

See `GITHUB_CHECKLIST.md` for detailed steps.
