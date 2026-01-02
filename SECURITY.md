# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in huesignal, please report it responsibly:

1. **Do not** open a public GitHub issue
2. Email the maintainers (details in pyproject.toml)
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We will respond within 48 hours and work with you to address the issue.

## Security Considerations

### Credential Storage

huesignal stores Hue Bridge credentials using the system keyring:
- Windows: Windows Credential Manager
- Linux: Secret Service API (GNOME Keyring, KWallet, etc.)
- macOS: Keychain

### Environment Variables

While credentials can be supplied via `HUESIGNAL_APP_KEY` environment variable for CI/CD, this should only be used in trusted environments. Never commit credentials to version control.

### Local Network Security

huesignal communicates with your Hue Bridge over your local network. Ensure your network is secured with:
- WPA2/WPA3 encryption
- Strong passwords
- Network isolation for IoT devices (recommended)

### API Key Management

The Hue Bridge API key grants full control over your lights. Treat it like a password:
- Never share it publicly
- Don't commit it to repositories
- Rotate it if compromised using `huesignal auth login` again

## Known Limitations

- Integration tests can control physical lights - use caution
- Detached processes may continue briefly after CLI exit
- mDNS discovery broadcasts device presence on local network
