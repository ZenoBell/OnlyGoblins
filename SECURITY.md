# Security and privacy

Session cookies and tokens can grant account access. Keep config files, browser exports, HAR captures, logs, creator lists, and downloaded media private. Credentials are stored locally in plaintext. Never commit a live config or attach it to a public issue.

Synthetic test credentials are marked with fixture or offline values and belong only in tests. Test and CI runs need no real accounts. Public release ZIPs must be built with build_exe.py from reviewed source, without copying a used application folder into the release.

Logs redact registered authentication values and signed URL queries. They may still reveal paths, creators, timestamps, or other personal context. Review and sanitize any excerpt before sharing it. Command-line tokens may appear in process listings and shell history.

For a suspected vulnerability, describe the affected version and a reproduction using synthetic data. Use GitHub's private vulnerability reporting on ZenoBell/FanGoblin if the maintainer has enabled it. Otherwise request a private reporting route without posting exploit credentials or personal data. Do not disclose real secrets in a public issue.

Automatic update checks are disabled in 1.0.0. Maintainers should review the updater and publish their own endpoint before enabling it. Download only content your account is authorized to access.
