# OnlyGoblins Cookie Helper

## 1.0.2 — Unreleased (prepared 2026-11-06)

- Fixed Firefox popup exports: the injected script path is now anchored at the
  extension root. Firefox previously attempted to load `popup/content_scripts/bcToken.js`
  and returned `[PAGE_ACCESS]` even with host access enabled.
- Reproduced the failure and verified the fix using an isolated Firefox profile and
  intercepted synthetic page; no real session data or live site request was needed.
- Added a regression assertion for resolving the script path from the popup.

## 1.0.1 — Unreleased (prepared 2026-11-06)

- Ignore duplicate unrelated cookies when validating the three exported auth cookies.
  Conflicting authentication values still fail safely.
- Show fixed, secret-free failure codes for tab access, page injection, cookie access,
  missing login/token data, and navigation instead of one generic error message.
- Add regression tests for duplicate cookies and safe error diagnostics.

## 1.0.0 — Unreleased (prepared 2026-11-06)

- Independent MIT-licensed integration based on upstream 2.3.0 at the commit in UPSTREAM.md.
- OnlyGoblins branding, mascot, purple/green/gold popup and independent browser identity.
- Explicit user-triggered export with copy/save actions; no persistent token collection.
- Firefox MV3 container-aware tab selection and Chromium MV3 configuration.
- Preserve real optional Auth UID; reject missing and ambiguous session fields.
- Deterministic allowlisted packages and synthetic tests.
- Desktop paste/file import validates locally and requires confirmation before saving.

The maintainer tested the original extension in Firefox Developer Mode.
That does not establish compatibility of this modified version; see SECURITY.md for verification limits.
