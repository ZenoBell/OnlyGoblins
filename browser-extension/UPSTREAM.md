# Provenance and maintenance

Imported on 2026-11-06 from [M-rcus/OnlyFans-Cookie-Helper](https://github.com/M-rcus/OnlyFans-Cookie-Helper)
at commit **6b2c941faecf10bf7af8e0adce350b2a990e5828**, whose manifests report **2.3.0**.
The latest upstream release tag inspected was **2.3.0**, commit
`f1c202c64ef67b43b9a3f67ef10201d92ecc85fd`; subsequent commits only updated upstream documentation.
Our independent extension version starts at **1.0.0**. It is unrelated to desktop versioning.

This directory contains the complete maintained runtime source, not a link or an
upstream binary. Upstream paths `popup/cookies.html`, `popup/cookies.js`,
`content_scripts/bcToken.js`, `icons/`, `.editorconfig`, and `LICENSE.md` are retained.
The cookie mapping and nested `auth` export structure derive from upstream.
`popup/export.js` separates export logic for testing. The real optional account-specific
Auth UID is now preserved rather than always exporting an empty value.

Intentional upstream omissions/replacements:

- `background/background.js`: removed persistent token storage and background collection.
  The selected tab is read only after Export. No `storage` permission remains.
- `lib/browser-polyfill.min.js`: unused minified dependency omitted; current Firefox
  `browser` and Chromium `chrome` APIs both provide the promises used here.
- `manifest_v2.json`: replaced with `manifest_firefox.json` using MV3, a new extension ID,
  container permission, and local-only data declaration. Chromium keeps `manifest.json`.
- `create_firefox_zip.sh`: replaced with a cross-platform standard-library Python build.
- Upstream cookie artwork and outdated screenshots/install claims: replaced with the
  supplied OnlyGoblins mascot and documentation. No upstream releases or Git internals imported.
- The legacy clipboard fallback and accumulating copy handlers were removed; one handler
  always uses the current export. Error display uses text, never HTML or raw exceptions.

## Updating independently

1. Fetch/clone upstream into a separate ignored scratch folder; never copy browser profiles or exports.
2. Diff against the pinned commit above. Review changes to cookies, `bcTokenSha`, manifests,
   permissions, and container behavior. Port only needed changes; retain explicit export and no-storage policy.
3. Record the reviewed commit and changes here and in CHANGELOG.md. Preserve LICENSE.md.
4. Increment the extension version in **both** manifests. Do not change the desktop version automatically.
5. Run the Python/Node tests and build instructions in README.md. Test both browsers with synthetic
   sessions first, then manually test an authorized account without recording secrets.
6. Review fresh package inventories and permissions. Signing/uploading is a separate maintainer action.

## Browser design references

- [Firefox scripting](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/scripting/executeScript)
- [Firefox containers](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Work_with_contextual_identities)
- [Firefox manifest/signing settings](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/manifest.json/browser_specific_settings)
- [Chromium scripting](https://developer.chrome.com/docs/extensions/reference/api/scripting)

Firefox configuration targets 140+ (including current ESR); Chromium targets 102+ API support.
Use a current supported browser. No service worker is needed because there is no background work.
Firefox Android's metadata minimum is 142 for its data-disclosure API; Android operation
has not been tested and the documented workflow targets desktop browsers.
