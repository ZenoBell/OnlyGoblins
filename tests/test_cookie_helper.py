"""Synthetic local-only Cookie Helper import and packaging regression tests."""
import importlib.util
import json
from pathlib import Path
import subprocess
import shutil
import zipfile
from unittest.mock import Mock

import pytest

from utils.cookie_helper import CookieHelperError, parse_cookie_helper_export

ROOT = Path(__file__).resolve().parents[1]


def payload(uid="synthetic-uid"):
    return {"auth": {"cookie": f"auth_id=123; sess=synthetic-session; auth_hash=; auth_uniq_123=; auth_uid_123={uid};",
                     "user_agent": "Synthetic Browser (Test; offline)", "x_bc": "synthetic-bc",
                     "email": "ignored", "password": "ignored"}}


def builder():
    spec = importlib.util.spec_from_file_location("extension_build", ROOT / "browser-extension/build.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("wrapped", [True, False])
@pytest.mark.parametrize("uid", ["", "synthetic-uid"])
def test_import_field_mapping(wrapped, uid):
    data = payload(uid)
    result = parse_cookie_helper_export(json.dumps(data if wrapped else data["auth"]))
    assert result == {"sess":"synthetic-session", "auth_id":"123", "auth_uid":uid,
                      "user_agent":"Synthetic Browser (Test; offline)", "x_bc":"synthetic-bc"}


@pytest.mark.parametrize("raw", ["{", "[]", "null", '{"auth":[]}', '{"auth":{},"auth":{}}', " " * 65537])
def test_malformed_json(raw):
    with pytest.raises(CookieHelperError):
        parse_cookie_helper_export(raw)


@pytest.mark.parametrize("field,value", [("cookie", None), ("cookie", 123), ("user_agent", ""),
                                         ("x_bc", []), ("x_bc", "secret\nheader")])
def test_invalid_fields_do_not_echo_values(field, value, caplog):
    data = payload()
    data["auth"][field] = value
    with pytest.raises(CookieHelperError) as error:
        parse_cookie_helper_export(json.dumps(data))
    assert "secret" not in str(error.value)
    assert caplog.text == ""


@pytest.mark.parametrize("cookie", ["sess=synthetic", "auth_id=123;", "auth_id=no; sess=x;",
    "auth_id=123; sess=x; sess=y;", "auth_id=123; sess=x; auth_uid_456=synthetic;", "auth_id=123; broken"])
def test_invalid_cookie_mapping(cookie):
    data = payload()
    data["auth"]["cookie"] = cookie
    with pytest.raises(CookieHelperError):
        parse_cookie_helper_export(json.dumps(data))


def test_confirmation_preserves_existing_fields_on_cancel(monkeypatch):
    from gui.widgets.onlyfans_auth import OnlyFansAuthSection
    section = Mock()
    monkeypatch.setattr("gui.widgets.onlyfans_auth.messagebox.askyesno", lambda *a, **k: False)
    assert not OnlyFansAuthSection.confirm_cookie_helper_import(section, parse_cookie_helper_export(json.dumps(payload())))
    section.save_to_config.assert_not_called()
    section.sess_entry.delete.assert_not_called()


def test_manifests_deterministic_packages_and_no_runtime_data(tmp_path):
    build = builder()
    build.validate()
    one = build.build(tmp_path / "one")
    two = build.build(tmp_path / "two")
    assert [p.read_bytes() for p in one] == [p.read_bytes() for p in two]
    for path in one:
        with zipfile.ZipFile(path) as archive:
            assert archive.testzip() is None
            assert set(archive.namelist()) == set(build.RUNTIME_FILES) | {"manifest.json"}
            manifest = json.loads(archive.read("manifest.json"))
            assert ("contextualIdentities" in manifest["permissions"]) == ("firefox" in path.name)
            assert b"Copyright (c) 2020-2024 Marcus" in archive.read("LICENSE.md")
            for name in archive.namelist():
                assert b"synthetic-session" not in archive.read(name)
    with pytest.raises(FileExistsError):
        build.build(tmp_path / "one")


def test_extension_has_no_secret_logging_or_network_code():
    build = builder()
    for name in build.RUNTIME_FILES:
        if name.endswith(".js"):
            source = (build.ROOT / name).read_text(encoding="utf-8")
            for forbidden in ("console.", "fetch(", "XMLHttpRequest", "WebSocket", "storage.local", "clipboard.read", "eval("):
                assert forbidden not in source


def test_extension_node_tests():
    if not shutil.which("node"):
        pytest.skip("Install Node 18+ to run browser API/DOM mocks")
    result = subprocess.run(["node", "--test", "tests/export.test.cjs", "tests/popup.test.cjs"],
                            cwd=ROOT / "browser-extension", capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.gui
def test_import_dialog_confirmation_and_restart(tmp_path, monkeypatch):
    import customtkinter as ctk
    from config.onlyfans_config import OnlyFansConfig, load_onlyfans_config
    from gui.widgets.onlyfans_auth import OnlyFansAuthSection
    from gui.widgets.cookie_helper_import import CookieHelperImportDialog
    config = OnlyFansConfig("1.0.0", config_path=tmp_path / "onlyfans_config.ini", sess="old-synthetic")
    app = ctk.CTk()
    try:
        section = OnlyFansAuthSection(app, config)
        section.pack()
        dialog = CookieHelperImportDialog(section)
        dialog.text.insert("1.0", json.dumps(payload("")))
        monkeypatch.setattr("gui.widgets.onlyfans_auth.messagebox.askyesno", lambda *a, **k: False)
        dialog.import_json()
        assert config.sess == "old-synthetic" and not config.config_path.exists()
        monkeypatch.setattr("gui.widgets.onlyfans_auth.messagebox.askyesno", lambda *a, **k: True)
        dialog.import_json()
        assert section.sess_entry.get() == "synthetic-session"
        restored = OnlyFansConfig("1.0.0", config_path=config.config_path)
        load_onlyfans_config(restored)
        assert restored.sess == "synthetic-session" and restored.auth_uid == ""
        assert restored.has_credentials()
    finally:
        app.destroy()
