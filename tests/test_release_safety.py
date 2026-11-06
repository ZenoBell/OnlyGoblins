# FanGoblin modifications by ZenoBell, 2026-11-06. See CHANGES_FROM_UPSTREAM.md.
"""Release isolation, credential redaction and package boundaries."""
from pathlib import Path
from unittest.mock import Mock
import zipfile

import pytest
import requests

import build_exe
from utils.privacy import redact_sensitive, register_secrets
from utils import web


def test_updates_disabled_without_any_network(monkeypatch):
    from updater.auto_update import check_for_update
    fetch = Mock(side_effect=AssertionError("Unexpected network"))
    monkeypatch.setattr(requests, "get", fetch)
    assert web.get_release_info_from_github("1.0.0") is None
    assert check_for_update("1.0.0", force=True) is None
    fetch.assert_not_called()


def test_enabled_endpoint_is_owned_by_onlygoblins(monkeypatch):
    monkeypatch.setattr("app_version.UPDATES_ENABLED", True)
    response = Mock(status_code=200)
    response.json.return_value = {"tag_name": "v1.0.1"}
    fetch = Mock(return_value=response)
    monkeypatch.setattr(requests, "get", fetch)
    assert web.get_release_info_from_github("1.0.0")["tag_name"] == "v1.0.1"
    assert fetch.call_args.args[0] == "https://api.github.com/repos/ZenoBell/FanGoblin/releases/latest"
    response.json.side_effect = ValueError("bad JSON")
    assert web.get_release_info_from_github("1.0.0") is None


def test_registered_credentials_and_signed_urls_are_redacted():
    secret = "synthetic-session-for-redaction"
    register_secrets(secret)
    value = f"failure {secret} https://example.invalid/media?signature=private-value"
    result = redact_sensitive(value)
    assert secret not in result
    assert "private-value" not in result
    assert "example.invalid/media" in result
    assert secret in value  # Redaction does not alter the caller's data.


def test_labelled_unregistered_credentials_are_redacted():
    result = redact_sensitive('sess=synthetic-cookie; auth_id=12345; x_bc=synthetic-bc')
    assert "synthetic-cookie" not in result
    assert "12345" not in result
    assert "synthetic-bc" not in result


def test_gui_file_logger_redacts_before_writing(tmp_path):
    from gui.logger import FileLogger
    path = tmp_path / "private-test.log"
    logger = FileLogger(path)
    logger.log("authorization_token=synthetic-token")
    logger.close()
    assert "synthetic-token" not in path.read_text()


def test_packaging_rejects_live_config_and_keeps_existing_zip(tmp_path):
    app = tmp_path / "OnlyGoblins"
    app.mkdir()
    (app / "OnlyGoblins.exe").write_bytes(b"synthetic-executable")
    (app / "onlyfans_config.ini").write_text("synthetic config")
    with pytest.raises(ValueError, match="Private runtime"):
        build_exe.create_distribution_zip(app, "OnlyGoblins", "1.0.0")
    (app / "onlyfans_config.ini").unlink()
    result = build_exe.create_distribution_zip(app, "OnlyGoblins", "1.0.0")
    before = result.read_bytes()
    with pytest.raises(FileExistsError):
        build_exe.create_distribution_zip(app, "OnlyGoblins", "1.0.0")
    assert result.read_bytes() == before
    with zipfile.ZipFile(result) as archive:
        assert archive.namelist() == ["OnlyGoblins/OnlyGoblins.exe"]


def test_branding_files_and_windows_version_metadata():
    from PIL import Image
    root = Path(build_exe.ROOT)
    with Image.open(root / "assets/branding/onlygoblins-icon.ico") as icon:
        assert icon.ico.sizes() == {(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)}
    metadata = build_exe.windows_version_info("1.0.0")
    assert "OnlyGoblins.exe" in metadata
    assert "(1, 0, 0, 0)" in metadata
    assert "ZenoBell" in metadata


def test_installed_ffmpeg_is_used_on_windows(monkeypatch):
    from utils.ffmpeg import get_ffmpeg_bin
    monkeypatch.setattr("utils.ffmpeg.shutil.which", lambda name: "C:/Tools/ffmpeg.exe")
    assert get_ffmpeg_bin() == "C:/Tools/ffmpeg.exe"


def test_missing_packaged_ffmpeg_has_actionable_error(monkeypatch):
    from utils.ffmpeg import get_ffmpeg_bin
    monkeypatch.setattr("utils.ffmpeg.shutil.which", lambda name: None)
    monkeypatch.setattr("sys.frozen", True, raising=False)
    with pytest.raises(RuntimeError, match="FFmpeg"):
        get_ffmpeg_bin()


def test_packaging_keeps_library_cookie_code_and_test_configuration():
    assert not build_exe.is_private_path(Path("_internal/curl_cffi/requests/cookies.py"))
    assert not build_exe.is_private_path(Path("pytest.ini"))
    assert build_exe.is_private_path(Path("cookies.json"))
    assert build_exe.is_private_path(Path("onlyfans_config.private.ini"))


def test_build_accepts_release_notes_from_a_published_tag(tmp_path):
    notes = tmp_path / "ReleaseNotes.md"
    notes.write_text("# OnlyGoblins\n\n### 1.0.0 - 2026-11-06\n\nRelease body\n")
    assert build_exe.read_release_notes("1.0.0", notes).notes == "Release body"


def test_gui_entry_point_runs_without_import_shadowing(monkeypatch):
    import fansly_downloader_gui as entry
    app = Mock()
    monkeypatch.setattr(entry, "create_app", Mock(return_value=app))
    monkeypatch.setattr("gui.logger.log", Mock())
    monkeypatch.setattr("gui.logger.close_logger", Mock())
    entry.main()
    app.run.assert_called_once()
