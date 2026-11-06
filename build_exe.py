# FanGoblin modifications by ZenoBell, 2026-11-06. See CHANGES_FROM_UPSTREAM.md.
"""Build the OnlyGoblins Windows GUI and local release artifacts.

This command builds locally. Publishing is a separate, explicit maintainer step.
"""

import argparse
from dataclasses import dataclass
from importlib import metadata
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import zipfile

from packaging.requirements import Requirement
from app_version import APP_NAME, APP_VERSION, REPOSITORY_URL

RELEASE_NOTES_PATH = Path("ReleaseNotes.md")
ROOT = Path(__file__).resolve().parent
PRIVATE_FILES = {
    "config.ini", "config_args.ini", "onlyfans_config.ini", "gui_state.json",
    "onlyfans_gui_state.json", "log_window_settings.json", "crop_settings.json",
    "watermark_blacklist.json", "download_history.json", "auth.json",
}
DOCS = ("LICENSE", "README.md", "CREDITS.md", "CHANGES_FROM_UPSTREAM.md", "THIRD_PARTY_NOTICES.md")
SOURCE_DIRS = {"api", "config", "docs", "download", "download_of", "errors", "fileio",
               "gui", "media", "pathio", "resources", "tests", "textio", "tools", "updater", "utils", ".github", "assets", "licenses"}
SOURCE_FILES = {".gitignore", "LICENSE", "README.md", "ReleaseNotes.md", "CREDITS.md",
                "CHANGES_FROM_UPSTREAM.md", "THIRD_PARTY_NOTICES.md", "SECURITY.md",
                "app_version.py", "build_exe.py", "build.ps1", "config.sample.ini",
                "onlyfans_config.sample.ini", "fansly_downloader_gui.py",
                "fansly_downloader_ng.py", "onlyfans_downloader.py", "mp4hash.py", "check.py",
                "requirements.txt", "requirements-dev.txt", "pytest.ini"}


@dataclass(frozen=True)
class ReleaseNotes:
    version: str
    notes: str


def find_unreleased_release_notes(content: str) -> ReleaseNotes:
    pattern = re.compile(r"^###\s+(\d+\.\d+\.\d+)\s*-\s*Unreleased\s*$", re.I | re.M)
    matches = list(pattern.finditer(content))
    if len(matches) != 1:
        raise ValueError("ReleaseNotes.md must contain one versioned unreleased heading, e.g. ### 1.0.0 - Unreleased")
    match = matches[0]
    next_heading = re.search(r"^###\s+", content[match.end():], re.M)
    end = match.end() + next_heading.start() if next_heading else len(content)
    notes = content[match.end():end].strip()
    if not notes:
        raise ValueError("The unreleased notes are empty")
    return ReleaseNotes(match.group(1), notes)


def read_unreleased_release_notes(path=RELEASE_NOTES_PATH):
    return find_unreleased_release_notes(Path(path).read_text(encoding="utf-8"))


def read_release_notes(version: str, path=RELEASE_NOTES_PATH):
    """Allow clean builds from both a prepared checkout and a published tag."""
    content = Path(path).read_text(encoding="utf-8")
    match = re.search(rf"^###\s+{re.escape(version)}\s*-\s*(?:Unreleased|\d{{4}}-\d{{2}}-\d{{2}})\s*$", content, re.I | re.M)
    if not match:
        raise ValueError(f"Missing release notes for {version}")
    next_heading = re.search(r"^###\s+", content[match.end():], re.M)
    end = match.end() + next_heading.start() if next_heading else len(content)
    notes = content[match.end():end].strip()
    if not notes:
        raise ValueError("Release notes are empty")
    return ReleaseNotes(version, notes)


def stamp_release_notes(content: str, version: str, release_date: str) -> str:
    pattern = re.compile(rf"^###\s+{re.escape(version)}\s*-\s*Unreleased\s*$", re.I | re.M)
    result, count = pattern.subn(f"### {version} - {release_date}", content, count=1)
    if count != 1:
        raise ValueError(f"Could not find unreleased heading for {version}")
    return result


def is_private_path(path: Path) -> bool:
    name = path.name.lower()
    return (name in PRIVATE_FILES or (name.endswith(".ini") and name not in {"config.sample.ini", "onlyfans_config.sample.ini", "pytest.ini"}) or name.endswith((".log", ".har", ".bak", ".backup", ".dump", ".dmp"))
            or (name.startswith(("auth_export", "onlygoblins-auth-export", "cookies")) and path.suffix.lower() in {".json", ".txt", ".har", ".cookies"}) or name.endswith("_history.json")
            or any(part in {".git", ".venv", "__pycache__", ".build-tools", ".pytest_cache"} for part in path.parts))


def verify_distribution(dist_dir: Path):
    """Fail closed when private runtime data has entered a build folder."""
    for path in dist_dir.rglob("*"):
        if path.is_file() and is_private_path(path.relative_to(dist_dir)):
            raise ValueError(f"Private runtime file in distribution: {path.relative_to(dist_dir)}")


def create_distribution_zip(dist_dir: Path, app_name: str, version: str | None = None) -> Path:
    verify_distribution(dist_dir)
    version = version or APP_VERSION
    zip_path = dist_dir.parent / f"{app_name}-Windows-x64-v{version}.zip"
    # Exclusive mode prevents overwriting a previously reviewed release.
    with zipfile.ZipFile(zip_path, "x", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(dist_dir.rglob("*")):
            if path.is_file():
                archive.write(path, str(Path(app_name) / path.relative_to(dist_dir)))
    return zip_path


def create_source_zip(output: Path, version: str):
    """Use an explicit source allowlist, never the working app directory."""
    path = output / f"{APP_NAME}-Source-v{version}.zip"
    files = [ROOT / name for name in SOURCE_FILES if (ROOT / name).is_file()]
    for directory in SOURCE_DIRS:
        files.extend(p for p in (ROOT / directory).rglob("*") if p.is_file())
    # Extension manifests/JS are explicit source entries, never arbitrary JSON exports.
    import runpy
    extension = runpy.run_path(str(ROOT / "browser-extension/build.py"))
    extension["validate"]()
    extension_files = {ROOT / "browser-extension" / name for name in extension["SOURCE_FILES"]}
    files.extend(extension_files)
    allowed_suffixes = {".py", ".py_old", ".md", ".txt", ".ini", ".png", ".ico", ".yml", ".yaml"}
    with zipfile.ZipFile(path, "x", zipfile.ZIP_DEFLATED) as archive:
        for file in sorted(set(files)):
            relative = file.relative_to(ROOT)
            if file in extension_files:
                archive.write(file, str(Path(f"{APP_NAME}-{version}") / relative))
                continue
            if relative.as_posix() in {"resources/fangoblin.ico", "resources/onlygoblins.ico"}:
                continue
            if is_private_path(relative):
                continue
            if file.suffix.lower() in {".png", ".ico"} and relative.parts[0] not in {"assets", "resources"}:
                continue
            if file not in [ROOT / name for name in SOURCE_FILES] and file.suffix not in allowed_suffixes:
                continue
            archive.write(file, str(Path(f"{APP_NAME}-{version}") / relative))
    return path


def collect_licenses(destination: Path):
    """Keep installed distribution notices, including notices for native components."""
    destination.mkdir()
    pending = [Requirement(line) for line in (ROOT / "requirements.txt").read_text().splitlines()
               if line.strip() and not line.startswith("#")]
    pending.append(Requirement("pyinstaller"))
    visited = set()
    inventory = []
    while pending:
        requirement = pending.pop()
        if requirement.marker and not requirement.marker.evaluate({"extra": ""}):
            continue
        key = requirement.name.lower().replace("_", "-")
        if key in visited or key == "pyffmpeg":
            continue
        visited.add(key)
        distribution = metadata.distribution(requirement.name)
        copied = []
        for file in distribution.files or []:
            if any(word in str(file).lower() for word in ("license", "copying", "notice")):
                source = Path(distribution.locate_file(file))
                if source.is_file():
                    target = destination / key / Path(str(file))
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target)
                    copied.append(str(file))
        inventory.append({"name": distribution.metadata["Name"], "version": distribution.version,
                          "license": distribution.metadata.get("License-Expression") or distribution.metadata.get("License", "See package notices"),
                          "notices": copied})
        pending.extend(Requirement(value) for value in distribution.requires or [])
    # The optional Windows LevelDB extension is included in this Windows build.
    distribution = metadata.distribution("plyvel-ci")
    for file in distribution.files or []:
        if "license" in str(file).lower():
            target = destination / "plyvel-ci" / Path(str(file))
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(distribution.locate_file(file), target)
    for name in ("LICENSE", "LICENSE.txt"):
        license_path = Path(sys.base_prefix) / name
        if license_path.exists():
            shutil.copy2(license_path, destination / "Python-LICENSE.txt")
            break
    (destination / "inventory.json").write_text(json.dumps(sorted(inventory, key=lambda d: d["name"]), indent=2), encoding="utf-8")


def windows_version_info(version):
    numbers = tuple(int(part) for part in version.split(".")) + (0,)
    return f'''VSVersionInfo(
  ffi=FixedFileInfo(filevers={numbers!r}, prodvers={numbers!r}, mask=0x3f,
    flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[StringFileInfo([StringTable('040904B0', [
    StringStruct('CompanyName', 'ZenoBell'),
    StringStruct('FileDescription', 'OnlyGoblins - Fansly and OnlyFans downloader'),
    StringStruct('FileVersion', '{version}'),
    StringStruct('InternalName', 'OnlyGoblins'),
    StringStruct('OriginalFilename', 'OnlyGoblins.exe'),
    StringStruct('ProductName', 'OnlyGoblins'),
    StringStruct('ProductVersion', '{version}'),
    StringStruct('LegalCopyright', 'Modified version by ZenoBell, 2026. Upstream authors credited in CREDITS.md. GPL-3.0.')
  ])]), VarFileInfo([VarStruct('Translation', [1033, 1200])])]
)'''


def build_exe(version: str | None = None, output: Path | None = None):
    import PyInstaller.__main__
    if sys.platform != "win32":
        raise RuntimeError("Build the Windows executable on Windows")
    version = version or APP_VERSION
    if version != APP_VERSION:
        raise ValueError("Build version must match app_version.py")
    notes = read_release_notes(version, ROOT / RELEASE_NOTES_PATH)
    output = Path(output).resolve() if output is not None else ROOT / "dist"
    output.mkdir(parents=True, exist_ok=True)
    app_dir = output / APP_NAME
    artifacts = [app_dir, output / f"{APP_NAME}-Windows-x64-v{version}.zip", output / f"{APP_NAME}-Source-v{version}.zip"]
    if any(path.exists() for path in artifacts):
        raise FileExistsError("Release output already exists. Move it to a backup location before rebuilding. Existing files have been preserved.")
    work_parent = ROOT / ".build-tools"
    work_parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="build-", dir=work_parent) as temporary:
        work = Path(temporary)
        version_file = work / "version.txt"
        version_file.write_text(windows_version_info(version), encoding="utf-8")
        args = [str(ROOT / "fansly_downloader_gui.py"), f"--name={APP_NAME}",
                "--onedir", "--windowed", f"--icon={ROOT / 'assets/branding/onlygoblins-icon.ico'}",
                f"--version-file={version_file}", f"--distpath={work / 'dist'}",
                f"--workpath={work / 'work'}", f"--specpath={work}",
                f"--paths={ROOT}", *[f"--add-data={ROOT / 'assets/branding' / name};assets/branding" for name in (
                    "onlygoblins-logo.png", "onlygoblins-icon.ico", "onlygoblins-icon.png", "onlygoblins-banner.png")],
                "--collect-all=customtkinter", "--collect-all=curl_cffi", "--hidden-import=plyvel",
                "--hidden-import=api.onlyfans_api", "--hidden-import=config.onlyfans_config",
                "--hidden-import=download_of", "--hidden-import=gui.tabs.onlyfans_tab",
                "--exclude-module=pyffmpeg", "--exclude-module=pytest", "--exclude-module=scipy",
                "--exclude-module=torch", "--exclude-module=easyocr", "--exclude-module=cv2",
                "--clean", "--noconfirm"]
        PyInstaller.__main__.run(args)
        built = work / "dist" / APP_NAME
        if not (built / f"{APP_NAME}.exe").is_file():
            raise RuntimeError("PyInstaller did not create the executable")
        for name in DOCS:
            shutil.copy2(ROOT / name, built / name)
        collect_licenses(built / "third-party-licenses")
        shutil.copytree(ROOT / "licenses", built / "third-party-licenses" / "project-snippets")
        verify_distribution(built)
        shutil.copytree(built, app_dir)
    binary_zip = create_distribution_zip(app_dir, APP_NAME, version)
    source_zip = create_source_zip(output, version)
    (output / f"{APP_NAME}-v{version}-release-notes.md").write_text(notes.notes.replace("assets/branding/", f"{REPOSITORY_URL}/raw/v{version}/assets/branding/") + "\n", encoding="utf-8")
    import hashlib
    checksums = [f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}" for path in (binary_zip, source_zip)]
    (output / "SHA256SUMS.txt").write_text("\n".join(checksums) + "\n", encoding="utf-8")
    print(f"Executable: {app_dir / (APP_NAME + '.exe')}")
    print(f"Windows ZIP: {binary_zip}")
    print(f"Source ZIP: {source_zip}")
    print(f"Publishing instructions: {REPOSITORY_URL}/blob/main/docs/RELEASING.md")
    return str(binary_zip)


def main():
    parser = argparse.ArgumentParser(description="Build OnlyGoblins locally. Publishing is a separate step.")
    parser.add_argument("--output", type=Path, help="Fresh output folder; existing artifacts are never overwritten")
    args = parser.parse_args()
    build_exe(output=args.output)


if __name__ == "__main__":
    main()
