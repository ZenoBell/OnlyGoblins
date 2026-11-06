# Cookie Helper security review — 2026-11-06

## Data flow and permissions

Popup open enumerates permitted OnlyFans tabs and Firefox container names only.
Explicit Export reads the selected tab's page token/user agent and its cookie store.
Explicit Copy writes the clipboard; explicit Save creates a local JSON download.
Closing/clearing the popup drops its references; JavaScript cannot guarantee secure memory erasure.
There are no listeners collecting credentials as you browse, and no persistent extension storage.

| Permission | Purpose |
| --- | --- |
| `https://onlyfans.com/*` | Exact HTTPS host only, no wildcard subdomains or unrelated sites |
| `cookies` | Read the selected session's cookies on explicit Export |
| `scripting` | Read `bcTokenSha` and user agent in the selected top-level tab on Export |
| `clipboardWrite` | Explicit Copy only; no clipboard read permission or monitoring |
| `contextualIdentities` (Firefox only) | Display container names; selected tab's cookieStoreId scopes cookies |

No `tabs` permission, downloads permission, storage, background worker, externally
connectable messages, native messaging, localhost service or analytics. Host permission
provides the limited tab metadata needed. Popup CSP forbids network connections and
remote scripts. There are no fetch/XHR/WebSocket calls. Cookie output is shown as text,
never inserted as HTML. No browser API exceptions, cookie values, tokens or raw JSON are logged.

Upstream persistent `st` → token storage and automatic content-script listeners were
replaced to meet the explicit-action policy. Selected container cookies and page storage
are read together. A URL/container change aborts export; contradictory duplicate cookies
are rejected. Same-tab login/navigation races cannot be eliminated completely; stop page
activity while exporting and use Test Connection. Private windows are deliberately unsupported.

Desktop parsing is bounded to 64 KiB, checks types/control characters/duplicates,
requires the four existing mandatory fields, and checks Auth UID account matching.
Errors contain fixed descriptions, never supplied values. Unknown metadata is discarded.
Entries and saved configuration are untouched until confirmation. Imported secrets are
registered with existing log redaction. The existing Test Connection exception dialog
now uses a fixed message so raw exceptions cannot expose an imported token.

## Verification scope

Automated tests use clearly synthetic strings, mocked browser APIs and DOM, and isolated
temporary desktop configs. They cover container store routing, no extraction on open,
export/copy/clear flows, failures, JSON mapping, cancellation, persistence, packaging,
permissions and deterministic ZIP contents. They do not establish live browser/API
compatibility or store acceptance. No real account tokens are used or included.

Builds use exact runtime file allowlists and include MIT notices. Auth export filenames
are ignored by Git and excluded by packaging. Builds never read browser profiles or
personal configs. Manual pre-release checks: load both browser builds, test two Firefox
containers with distinct authorized sessions, copy/save/import/cancel/restart, and inspect
extension diagnostics without sharing credentials. Existing screenshots contained old
branding/session output, so no upstream screenshot was imported.

Firefox declares no automatic data collection/transmission. User-directed local exports
are the sole purpose; review Mozilla's current submission disclosures when signing.
Saved JSON, clipboard history and the desktop INI remain sensitive; secure them yourself.
