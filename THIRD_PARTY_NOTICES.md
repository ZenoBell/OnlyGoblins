# Third-party notices

OnlyGoblins is GPL-3.0. Dependency licenses apply to their own components and original notices remain applicable. The unchanged inherited LICENSE includes the Avnsx notice. Attribution and modification dates are in CREDITS.md.

## Python components and native libraries

The Windows build collects available LICENSE, COPYING and NOTICE files from runtime distributions and their installed dependencies. See `third-party-licenses/inventory.json` in the release for exact versions and `third-party-licenses/` for texts. The package contains Python and Tcl/Tk runtime code, CustomTkinter and its font assets, Pillow and image libraries, Requests and TLS/network dependencies, curl_cffi and its libcurl/native dependencies, NumPy/ImageHash, Loguru, Rich, m3u8, dateutil, psutil, websockets, strenum, and optional plyvel-ci/LevelDB components. Their own licenses and notices must accompany redistribution.

The build copies the Python distribution license when provided by the build runtime. PyInstaller supplies a bootloader exception for generated bundles and keeps its own license. Runtime versions depend on the build environment, so the included inventory is authoritative for a particular ZIP. Retain all shipped notice files when redistributing.

## OF-Scraper adaptation

The OnlyFans authentication module retains its inherited adaptation notice. The MIT license from the referenced OF-Scraper fork, including its datawhores copyright notice, is in `licenses/OF-Scraper-MIT.txt` and copied into the binary package.

## OnlyGoblins Cookie Helper

The separately packaged browser extension derives from M-rcus/OnlyFans-Cookie-Helper
2.3.0. Its original MIT copyright/license is preserved in `browser-extension/LICENSE.md`;
see `browser-extension/UPSTREAM.md` for the exact commit and changes. Extension code
modifications are MIT; the reused mascot retains GPL-3.0 artwork terms and includes
`icons/LICENSE.txt`. No upstream polyfill or proprietary platform icon is shipped.
The desktop importer is original OnlyGoblins GPL-3.0 code.

## FFmpeg

The legacy pyffmpeg wrapper has its own license and embeds a compressed FFmpeg executable. The public OnlyGoblins Windows package excludes that wrapper and embedded executable because exact binary provenance and corresponding source were not established. Install FFmpeg separately for streaming conversion. Distributors who choose to bundle FFmpeg must review the licenses and corresponding-source requirements for their exact build and enabled components. Source installations preserve the existing wrapper fallback.

## Artwork and inherited documents

The OnlyGoblins logo is maintainer-supplied artwork with confirmed redistribution permission. Its original file and exact cropped derivatives are included under the project's GPL-3.0 terms. Inherited `resources/` artwork is preserved as upstream source material and is excluded from the Windows application. A separately authored technical reference PDF remains on the local filesystem but is excluded from Git and release archives until separate redistribution permission is established. Other inherited text references keep their applicable notices.

For a binary release, publish the matching OnlyGoblins source ZIP alongside the binary and retain the source and notices for any separately redistributed dependency components. This inventory records distribution contents and is not a substitute for reviewing licenses of additional components you introduce.
