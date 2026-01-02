#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Automated version bump and publish script for huesignal

.DESCRIPTION
    This script automates the process of:
    1. Bumping the version in pyproject.toml
    2. Creating a git commit and tag
    3. Pushing to GitHub to trigger the publish workflow

.PARAMETER BumpType
    Type of version bump: major, minor, or patch (default: patch)

.PARAMETER DryRun
    If specified, shows what would be done without making changes

.EXAMPLE
    .\Publish.ps1 -BumpType patch
    Bumps patch version (0.1.0 -> 0.1.1)

.EXAMPLE
    .\Publish.ps1 -BumpType minor
    Bumps minor version (0.1.0 -> 0.2.0)

.EXAMPLE
    .\Publish.ps1 -BumpType major -DryRun
    Shows what a major version bump would do (0.1.0 -> 1.0.0)
#>

[CmdletBinding()]
param(
    [Parameter()]
    [ValidateSet('major', 'minor', 'patch')]
    [string]$BumpType = 'patch',

    [Parameter()]
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Color output functions
function Write-Success { param($Message) Write-Host "✓ $Message" -ForegroundColor Green }
function Write-Info { param($Message) Write-Host "ℹ $Message" -ForegroundColor Cyan }
function Write-Warning { param($Message) Write-Host "⚠ $Message" -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host "✗ $Message" -ForegroundColor Red }

# Check if we're in the right directory
if (-not (Test-Path "pyproject.toml")) {
    Write-Error "pyproject.toml not found. Run this script from the repository root."
    exit 1
}

Write-Info "Starting publish workflow for huesignal..."
Write-Info "Bump type: $BumpType"
if ($DryRun) {
    Write-Warning "DRY RUN MODE - No changes will be made"
}

# Check git status
Write-Info "Checking git status..."
$gitStatus = git status --porcelain
if ($gitStatus -and -not $DryRun) {
    Write-Error "Working directory is not clean. Commit or stash changes first."
    Write-Host $gitStatus
    exit 1
}
Write-Success "Working directory is clean"

# Get current version from pyproject.toml
Write-Info "Reading current version..."
$pyprojectContent = Get-Content "pyproject.toml" -Raw
if ($pyprojectContent -match 'version\s*=\s*"(\d+)\.(\d+)\.(\d+)"') {
    $major = [int]$matches[1]
    $minor = [int]$matches[2]
    $patch = [int]$matches[3]
    $currentVersion = "$major.$minor.$patch"
    Write-Success "Current version: $currentVersion"
} else {
    Write-Error "Could not parse version from pyproject.toml"
    exit 1
}

# Calculate new version
switch ($BumpType) {
    'major' {
        $major++
        $minor = 0
        $patch = 0
    }
    'minor' {
        $minor++
        $patch = 0
    }
    'patch' {
        $patch++
    }
}
$newVersion = "$major.$minor.$patch"
$tagName = "v$newVersion"

Write-Info "New version will be: $newVersion"
Write-Info "Git tag will be: $tagName"

# Check if tag already exists
$existingTag = git tag -l $tagName
if ($existingTag) {
    Write-Error "Tag $tagName already exists!"
    exit 1
}

if ($DryRun) {
    Write-Warning "DRY RUN: Would update version from $currentVersion to $newVersion"
    Write-Warning "DRY RUN: Would create git tag $tagName"
    Write-Warning "DRY RUN: Would push to origin to trigger publish workflow"
    exit 0
}

# Confirm with user
Write-Host ""
Write-Warning "About to:"
Write-Host "  1. Update version in pyproject.toml: $currentVersion → $newVersion"
Write-Host "  2. Create git commit and tag: $tagName"
Write-Host "  3. Push to GitHub (triggers PyPI publish via trusted publisher)"
Write-Host ""
$confirm = Read-Host "Continue? (y/N)"
if ($confirm -ne 'y' -and $confirm -ne 'Y') {
    Write-Info "Cancelled by user"
    exit 0
}

# Update version in pyproject.toml
Write-Info "Updating pyproject.toml..."
$pyprojectContent = $pyprojectContent -replace 'version\s*=\s*"\d+\.\d+\.\d+"', "version = `"$newVersion`""
Set-Content "pyproject.toml" -Value $pyprojectContent -NoNewline
Write-Success "Updated version to $newVersion in pyproject.toml"

# Update fallback version in __init__.py
Write-Info "Updating fallback version in __init__.py..."
$initPath = "src/huesignal/__init__.py"
$initContent = Get-Content $initPath -Raw
$initContent = $initContent -replace '__version__\s*=\s*"\d+\.\d+\.\d+"', "__version__ = `"$newVersion`""
Set-Content $initPath -Value $initContent -NoNewline
Write-Success "Updated fallback version in __init__.py"

# Update uv.lock
Write-Info "Updating uv.lock..."
try {
    uv lock 2>&1 | Out-Null
    Write-Success "Updated uv.lock"
} catch {
    Write-Warning "Failed to update uv.lock - you may need to run 'uv lock' manually"
}

# Create git commit
Write-Info "Creating git commit..."
git add pyproject.toml uv.lock src/huesignal/__init__.py
git commit -m "chore: bump version to $newVersion"
Write-Success "Created commit"

# Create git tag
Write-Info "Creating git tag $tagName..."
git tag -a $tagName -m "Release version $newVersion"
Write-Success "Created tag $tagName"

# Push to GitHub
Write-Info "Pushing to GitHub..."
Write-Warning "This will trigger the PyPI publish workflow via GitHub Actions trusted publisher"
Write-Host ""
$confirmPush = Read-Host "Push now? (y/N)"
if ($confirmPush -ne 'y' -and $confirmPush -ne 'Y') {
    Write-Warning "Changes committed and tagged locally, but not pushed"
    Write-Info "To push manually later, run:"
    Write-Host "  git push origin main && git push origin $tagName"
    exit 0
}

git push origin main
git push origin $tagName
Write-Success "Pushed to GitHub"

Write-Host ""
Write-Success "✨ Release process initiated!"
Write-Info "Monitor the workflow at: https://github.com/ThomasRohde/huesignal/actions"
Write-Info "Package will be published to: https://pypi.org/project/huesignal/"
Write-Host ""
Write-Info "After publishing, you can install with: pip install huesignal==$newVersion"
