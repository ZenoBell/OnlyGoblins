# OnlyGoblins Cookie Helper

<img src="icons/onlygoblins.png" alt="OnlyGoblins mascot" width="96">

An independently maintained, MIT-licensed browser extension included in OnlyGoblins.
Export your own signed-in OnlyFans session, then explicitly import it into the desktop GUI.
Based on [M-rcus/OnlyFans-Cookie-Helper](https://github.com/M-rcus/OnlyFans-Cookie-Helper)
2.3.0; exact provenance and maintenance instructions are in [UPSTREAM.md](UPSTREAM.md).
No browser store publication is claimed. OnlyFans/Fansly do not endorse this project.

## Build and validate

From the OnlyGoblins repository root (Python 3.11+; Node 18+ for JS tests only):

```powershell
python browser-extension/build.py --check
node --test browser-extension/tests/export.test.cjs browser-extension/tests/popup.test.cjs
python tools/run_tests.py
python browser-extension/build.py
```

No npm packages, bundlers, signing keys, or network calls are needed. Output is in
`browser-extension/dist/`: a Firefox ZIP and unpacked directory, a Chromium ZIP and
unpacked directory, and SHA256SUMS.txt. ZIPs use sorted explicit file lists and fixed
timestamps. Rebuilding refuses to overwrite existing packages; use `--output path/to/new-folder`.

## Firefox temporary installation

1. Use Firefox 140+ and build/extract the Firefox package.
2. Visit `about:debugging#/runtime/this-firefox` → **Load Temporary Add-on**.
3. Select `manifest.json` in `OnlyGoblins-Cookie-Helper-firefox-v1.0.2/`.
4. Allow access to `https://onlyfans.com` if prompted. Pin the helper if desired.

Temporary extensions disappear on browser restart. The ZIP is **unsigned**, not a
permanently installable signed XPI. For permanent distribution, the maintainer must
submit the Firefox ZIP through Mozilla's applicable signing process, supply required
policy disclosures, and distribute the resulting signed file. Acceptance is not guaranteed.
No signing keys or submission automation are included.

## Chromium unpacked installation

1. Use a current Chromium browser and build/extract the Chromium package.
2. Visit `chrome://extensions` (Edge: `edge://extensions`). Enable **Developer mode**.
3. Select **Load unpacked** and choose `OnlyGoblins-Cookie-Helper-chromium-v1.0.2/`.
4. Allow OnlyFans site access. No CRX or Chrome Web Store listing is provided.

## Export and import

1. Sign in to your own OnlyFans account normally and let the page fully load.
2. Open the helper. Select the desired OnlyFans tab; Firefox labels show its container.
   Container accounts need an open OnlyFans tab in that container. Private windows are unsupported.
3. Click **Export this session**. Opening the popup alone does not collect credentials.
4. Click **Copy JSON** or **Save JSON file**. Clear removes popup data, not your clipboard or disk file.
5. In OnlyGoblins → OnlyFans authentication, click **Import from OnlyGoblins Cookie Helper**.
6. Paste JSON or choose the exported file, click **Validate and import**, then confirm replacement/saving.
7. Run the existing **Test Connection**. Manual credential entry remains available.

The importer maps `auth.cookie`'s `sess`, `auth_id`, and matching `auth_uid_<auth_id>`
to the existing desktop fields; `auth.user_agent` and `auth.x_bc` map directly.
An absent/empty Auth UID clears the previous UID after confirmation. Legacy metadata
such as username/email/password is not saved. Existing configuration filenames and formats stay unchanged.

**Treat exported JSON like a password.** It contains reusable session credentials.
Never share it, paste it into a website, commit it, or attach it to an issue. Clipboard
history/cloud clipboard and your downloads folder can retain copies. Clear history and
remove exports after use. OnlyGoblins intentionally saves confirmed credentials in its
existing local INI file; protect that file. This helper does not bypass subscriptions,
2FA login, DRM or access controls, and expired sessions must be exported again.

## Source layout and security

If Firefox shows `[PAGE_ACCESS]` on 1.0.1, install 1.0.2: it corrects the popup's
script path. Enabling private-window access or restricted-site access is not required.

If export fails, version 1.0.1 displays a fixed diagnostic code, such as `[PAGE_ACCESS]`,
`[COOKIE_ACCESS]`, `[LOGIN]` or `[TOKEN]`. Follow the accompanying instruction. When
reporting a problem, share only this code and your browser version, never the exported
JSON, cookies or tokens. Unrelated duplicate site cookies no longer prevent export;
conflicting values for the required authentication cookies still fail safely.

- `popup/`: local HTML/CSS, tab/container selection, export controls and mapping.
- `content_scripts/bcToken.js`: one-shot read of the selected page's `bcTokenSha` and user agent.
- `manifest.json` / `manifest_firefox.json`: separate MV3 configurations.
- `build.py`: deterministic allowlisted distribution generation.
- `tests/`: synthetic browser API/DOM tests; no real tokens.

No telemetry, remote scripts, storage permission, network requests, clipboard reading,
background scripts, native messaging or local servers. See [SECURITY.md](SECURITY.md),
[CHANGELOG.md](CHANGELOG.md), [NOTICE.md](NOTICE.md) and the original [MIT license](LICENSE.md).
The parent OnlyGoblins project remains GPL-3.0.
