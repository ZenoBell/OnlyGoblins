"""Dependency-free, deterministic Cookie Helper packaging. Never reads runtime data."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parent
RUNTIME_FILES = (
    "popup/cookies.html", "popup/cookies.css", "popup/cookies.js", "popup/export.js",
    "content_scripts/bcToken.js", "icons/onlygoblins.png", "icons/onlygoblins-48.png",
    "icons/onlygoblins-128.png", "icons/LICENSE.txt", "LICENSE.md", "NOTICE.md",
)
SOURCE_FILES = RUNTIME_FILES + (
    "manifest.json", "manifest_firefox.json", "build.py", "README.md", "CHANGELOG.md",
    "SECURITY.md", "UPSTREAM.md", ".editorconfig", "tests/export.test.cjs",
    "tests/popup.test.cjs",
)


def validate():
    manifests = {}
    for browser, filename in (("chromium", "manifest.json"), ("firefox", "manifest_firefox.json")):
        manifest = json.loads((ROOT / filename).read_text(encoding="utf-8"))
        assert manifest["manifest_version"] == 3
        assert manifest["name"] == "OnlyGoblins Cookie Helper"
        assert re.fullmatch(r"\d+\.\d+\.\d+", manifest["version"])
        assert manifest["host_permissions"] == ["https://onlyfans.com/*"]
        expected = {"cookies", "scripting", "clipboardWrite"}
        if browser == "firefox":
            expected.add("contextualIdentities")
            assert manifest["browser_specific_settings"]["gecko"]["id"] == "onlygoblins-cookie-helper@zenobell"
        else:
            assert "browser_specific_settings" not in manifest
        assert set(manifest["permissions"]) == expected
        assert "background" not in manifest and "content_scripts" not in manifest
        assert manifest["action"]["default_popup"] in RUNTIME_FILES
        assert "connect-src 'none'" in manifest["content_security_policy"]["extension_pages"]
        for file in manifest["icons"].values():
            assert file in RUNTIME_FILES
        manifests[browser] = manifest
    assert manifests["firefox"]["version"] == manifests["chromium"]["version"]
    for name in SOURCE_FILES:
        assert (ROOT / name).is_file(), f"Missing extension source: {name}"
    return manifests


def package_bytes(manifest):
    result = {name: (ROOT / name).read_bytes() for name in RUNTIME_FILES}
    result["manifest.json"] = (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    return result


def build(output):
    manifests = validate()
    version = manifests["firefox"]["version"]
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    artifacts = {}
    for browser, manifest in manifests.items():
        name = f"OnlyGoblins-Cookie-Helper-{browser}-v{version}"
        artifacts[browser] = (output / name, output / f"{name}.zip", package_bytes(manifest))
    if any(folder.exists() or archive.exists() for folder, archive, _ in artifacts.values()):
        raise FileExistsError("Output exists; choose another output folder. Existing files are preserved.")
    checksums = []
    for folder, archive, files in artifacts.values():
        folder.mkdir()
        with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
            for name, data in sorted(files.items()):
                target = folder / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
                entry = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
                entry.compress_type = zipfile.ZIP_DEFLATED
                entry.external_attr = 0o100644 << 16
                entry.create_system = 3
                bundle.writestr(entry, data, compresslevel=9)
        checksums.append(f"{hashlib.sha256(archive.read_bytes()).hexdigest()}  {archive.name}")
    (output / "SHA256SUMS.txt").write_text("\n".join(checksums) + "\n", encoding="utf-8")
    return [archive for _, archive, _ in artifacts.values()]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Validate without producing files")
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    if args.check:
        validate()
        print("Extension validation passed.")
    else:
        for archive in build(args.output):
            print(archive)
