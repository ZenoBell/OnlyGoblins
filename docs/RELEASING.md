# First public OnlyGoblins release

Target repository is `ZenoBell/FanGoblin`. Version is `1.0.0` and the first release tag is `v1.0.0`. The commands below are instructions for the maintainer. No push, tag publication or GitHub release is performed by the build script.

## Prepare source and inspect the staged files

Run in PowerShell from this project folder.

```powershell
Set-Location 'PATH-TO-YOUR-OnlyGoblins-CHECKOUT'
git status --short
git diff --cached --stat
git diff --cached
```

The local repository has a `main` branch, an existing initial commit, and the configured origin shown below. Review your changes, particularly the absence of live configs, logs, exports and media. Keep the original GPL license, credits and logo. Replace the local path with your checkout path on another machine.

## Test and build

```powershell
Set-Location 'PATH-TO-YOUR-OnlyGoblins-CHECKOUT'
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe tools/run_tests.py
.\.venv\Scripts\python.exe -X utf8 build_exe.py
```

The build refuses to overwrite existing `dist/OnlyGoblins` or release archives. Move an old output to a separate backup folder before rebuilding. Inspect both source and binary ZIPs, the included notices and SHA256SUMS.txt. Install FFmpeg on PATH for streaming conversion. Test the executable from an empty profile and with a local copy of existing settings before publication. Do not upload a folder after entering credentials into it.

## Connect and push the repository

The existing origin is `https://github.com/ZenoBell/FanGoblin.git`. The application is named OnlyGoblins, while this configured repository slug remains authoritative. Inspect the remote and changes before committing or pushing.

```powershell
git remote -v
git diff --stat
git add -- .
git diff --cached --stat
git commit -m "Rebrand application to OnlyGoblins"
git push origin main
```

Confirm your intended Git author identity before committing. The build script performs local builds only. Reconcile any remote changes deliberately without a force push.

## Publish the first release

Review the generated release notes. Stamp `### 1.0.0 - Unreleased` in ReleaseNotes.md with the actual publication date, then commit and push that documentation change before creating the release tag. Keep the independent version at 1.0.0.

```powershell
git add ReleaseNotes.md
git commit -m "Finalize OnlyGoblins 1.0.0 release notes"
git push origin main
git tag -a v1.0.0 -m "OnlyGoblins 1.0.0"
git push origin v1.0.0
gh release create v1.0.0 --repo ZenoBell/FanGoblin --verify-tag --title "OnlyGoblins 1.0.0" --notes-file dist/OnlyGoblins-v1.0.0-release-notes.md dist/OnlyGoblins-Windows-x64-v1.0.0.zip dist/OnlyGoblins-Source-v1.0.0.zip dist/SHA256SUMS.txt
```

Install and authenticate GitHub CLI before using `gh`. Alternatively open this repository's Releases page, create a release from `v1.0.0`, paste the generated release notes, and upload the same three files. Release notes on GitHub use absolute repository paths for artwork so the logo renders outside the repository file viewer. The binary package and matching source should both be available.

Do not enable in-app updates merely to publish 1.0.0. Updates are gated by `UPDATES_ENABLED = False` in app_version.py. A later release can enable them after reviewing the correct endpoint, archive compatibility and recovery behavior.

## Repository presentation

Suggested description is **A dark-theme Fansly and OnlyFans downloader with optional Fansly setup, GUI and CLI workflows.**

Suggested topics are `python`, `windows`, `gui`, `customtkinter`, `downloader`, `fansly`, `onlyfans`, `media-downloader` and `gpl-3-0`.

For GitHub's social preview, open repository Settings, find Social preview and upload `assets/branding/onlygoblins-banner.png`. The supplied banner is 1280Ã—640. The full logo is used in the README and the cropped face icon is embedded in the executable.
