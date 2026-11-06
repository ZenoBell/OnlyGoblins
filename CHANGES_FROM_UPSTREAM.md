# Changes from upstream

## Cookie Helper integration — 2026-11-06

- Added complete maintained browser extension source based on M-rcus's MIT-licensed
  OnlyFans Cookie Helper 2.3.0; exact commit, omissions and modifications are in
  `browser-extension/UPSTREAM.md`.
- Added local paste/file JSON validation and confirmed credential import to the existing
  OnlyFans GUI. Manual entry, configuration formats, signing and download logic are unchanged.
- Added explicit-export MV3 Firefox/Chromium builds, container-aware token selection,
  synthetic tests and privacy documentation. No automatic browser/desktop connection.

OnlyGoblins is based on Frangus90/Fansly-OF-Downloader v1.8.8 at commit `4777ff4f022126830aa89edab3ae437e5c56a104`, with earlier prof79 and Avnsx lineage. The changes below are established from the local patch and source comparison. Independent maintenance and release preparation are dated 2026-11-06.

## Existing fork improvements

- Missing Fansly credentials open the OnlyFans tab directly. The Fansly wizard is launched explicitly and includes Skip Fansly Setup. Dismissing it keeps the main application open.
- Fansly configuration defaults can be loaded into memory without creating or rewriting an account file at GUI startup. Config parser state is isolated per instance.
- Fansly wizard saves merge with existing configuration instead of overwriting unrelated settings.
- OnlyFans credentials and GUI settings persist independently, edited credentials invalidate the cached API client, and fractional request delays are preserved.
- OnlyFans requests use the curl_cffi browser-compatible HTTP client with the user's own credentials. Current signing-rule field formats are normalized. Only explicitly supplied optional auth cookies are sent.
- Offline GUI, authentication, persistence, packaging, and download-fixture tests were added.

## OnlyGoblins 1.0.0 release preparation

- New application name, version, product metadata, executable and ZIP names, official logo, face icon, README and release documentation.
- OnlyGoblins release URLs point to ZenoBell/FanGoblin. In-app update checks are disabled for the first independent release.
- CLI session previews, raw argument logging, and a Fansly authentication error's token dump were removed. Shared redaction covers log output and signed URL queries.
- Release builds use temporary build directories, exclude private runtime files, include component notices and source, and refuse to overwrite existing releases.
- The Windows package omits the opaque FFmpeg executable embedded by pyffmpeg. Streaming conversion uses an FFmpeg installation on PATH. Source installations retain their existing fallback.
- Requests was updated past the advisory-affected version found during the release audit. Runtime packaging requirements and test dependencies are declared.
- Documentation distinguishes the implemented config-driven OnlyFans CLI and message incremental history from unsupported CLI flags and timeline cursor claims.

Configuration filenames, creator state, download history formats, and existing platform tabs are retained. Download algorithms, deduplication, and authentication/signing algorithms were not rewritten for branding.

## Verification scope

The maintainer reports successful authentication and real media downloads. Earlier local verification also observed a successful authenticated account response in the Windows GUI. Automated tests use synthetic data. No particular creator, content count, speed, or future compatibility guarantee is claimed.

## OnlyGoblins branding update — 2026-11-06

The project was previously prepared locally as FanGoblin. OnlyGoblins is now the user-facing name. The configured repository remains ZenoBell/FanGoblin. The maintainer supplied the new original artwork, used unchanged in the README and cropped for the executable icon. Download, authentication and configuration logic are unchanged by this branding update.
