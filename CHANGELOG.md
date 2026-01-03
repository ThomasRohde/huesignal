# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of huesignal
- CLI interface with Typer
- Bridge discovery via mDNS and Hue discovery endpoint
- Authentication with secure keyring storage
- Light listing and selection by name
- Effect framework with state capture/restore
- Built-in effects: blink, pulse, breathe, rainbow
- Fire-and-forget runner for time-based effects
- Automation samples for common use cases
- Doctor command for diagnostics
- Comprehensive test suite
- GitHub Actions CI workflow
- Pre-commit hooks for code quality
- **NEW: Semantic effect presets** (`success`, `error`, `warning`, `working`, `claim`, etc.)
- **NEW: Effect demo command** (`huesignal effect demo`) for visual exploration
- **NEW: Universal brightness format support** in YAML (decimal/percentage/raw)
- **NEW: Smart error messages** with "Did you mean?" suggestions
- **NEW: Effect name fuzzy matching** for typo correction

### Changed
- **IMPROVED: Getting started wizard** now works correctly (fixed authentication bug)
- **IMPROVED: Error messages** now provide helpful suggestions and examples
- **IMPROVED: YAML brightness validation** accepts decimal (0.0-1.0) and percentage (0-100) formats
- **IMPROVED: Brightness error messages** include format suggestions

### Fixed
- **CRITICAL: Getting started wizard** - Fixed `store_app_key()` call with wrong number of arguments
- **CRITICAL: Getting started wizard** - Fixed bridge discovery data format access
- **FIXED: YAML brightness format** - Now accepts decimal notation consistently with CLI
- **FIXED: Effect name validation** - Better error messages with available effects list

## [0.1.0] - 2026-01-02

### Added
- Initial alpha release for testing and feedback
