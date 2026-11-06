# FanGoblin modifications by ZenoBell, 2026-11-06. See CHANGES_FROM_UPSTREAM.md.
"""Offline regression tests using real Tk widgets and isolated working directories."""

import gc
from configparser import ConfigParser
from pathlib import Path
from threading import Event
from tkinter import TclError
from unittest.mock import Mock

import customtkinter as ctk
import pytest
import requests
from curl_cffi import requests as browser_requests

from api.onlyfans_auth import OnlyFansAuth
from gui.app import create_app
from gui.logger import close_logger

pytestmark = pytest.mark.gui


@pytest.fixture
def launch(tmp_path, monkeypatch):
    import os, sys
    if sys.platform != "win32" and not os.environ.get("DISPLAY") and sys.platform != "darwin":
        pytest.skip("GUI tests need a desktop display")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("gui.log_settings.SETTINGS_FILE", tmp_path / "log_window_settings.json")

    def offline(*args, **kwargs):
        pytest.fail("Unexpected network request")

    monkeypatch.setattr(requests.Session, "request", offline)
    monkeypatch.setattr(browser_requests.Session, "request", offline)
    monkeypatch.setattr("gui.window.check_for_update_async", Mock())
    windows = []

    def start():
        gc.collect()  # Free destroyed Tcl interpreters before creating another.
        app = create_app()
        app.update()
        windows.append(app)
        return app

    yield start
    for app in windows:
        try:
            if app.winfo_exists():
                app.destroy()
        except TclError:
            pass  # The restart test already closed this Tcl application.
    windows.clear()
    gc.collect()
    close_logger()


def children(widget):
    for child in widget.winfo_children():
        yield child
        yield from children(child)


def click(widget, label):
    button = next(child for child in children(widget)
                  if isinstance(child, ctk.CTkButton) and child.cget("text") == label)
    button.invoke()


@pytest.mark.parametrize("existing", [None, "", "[MyAccount]\n", (
    "[MyAccount]\nauthorization_token=ReplaceMe\nuser_agent=ReplaceMe\n"
    "[Options]\nuse_folder_suffix=false\n[Custom]\nkeep=unchanged\n"
)])
def test_unconfigured_startup(launch, existing, monkeypatch):
    path = Path("config.ini")
    if existing is not None:
        path.write_text(existing, encoding="utf-8")
    connect = Mock()
    monkeypatch.setattr("gui.widgets.auth_section.AuthSection.test_connection", connect)
    app = launch()
    app.after(650, app.quit)
    app.mainloop()
    assert app.tab_view.get() == "OnlyFans"
    assert app.of_sections["auth"].sess_entry.winfo_viewable()
    assert app.grab_current() is None
    assert not app.of_app_state.config.has_credentials()
    assert not app.sections["auth"].token_entry.get()
    connect.assert_not_called()
    app.on_close()
    if existing is None:
        assert not path.exists()
    else:
        assert path.read_text(encoding="utf-8") == existing


@pytest.mark.parametrize("dismiss", ["skip", "window_close"])
def test_dismiss_optional_wizard(launch, dismiss, monkeypatch):
    app = launch()
    app.tab_view.set("Fansly")
    def dismiss_dialog(wizard):
        if dismiss == "skip":
            click(wizard.pages[0], "Skip Fansly Setup")
        else:
            wizard.tk.call(wizard.protocol("WM_DELETE_WINDOW"))

    monkeypatch.setattr(app, "wait_window", dismiss_dialog)
    click(app.sections["auth"], "Set Up Fansly...")
    assert app.winfo_exists()
    assert app.grab_current() is None
    assert not Path("config.ini").exists()
    if dismiss == "skip":
        assert app.tab_view.get() == "OnlyFans"
    app.show_onlyfans_tab()
    assert app.of_sections["auth"].sess_entry.get() == ""


def test_onlyfans_auth_and_restart(launch, monkeypatch):
    app = launch()
    auth = app.of_sections["auth"]
    click(auth, "How to get OF credentials?")
    guide = auth.grab_current()
    assert guide.title() == "How to Get OnlyFans Credentials"
    click(guide, "Close")

    info, error = Mock(), Mock()
    monkeypatch.setattr("tkinter.messagebox.showinfo", info)
    monkeypatch.setattr("tkinter.messagebox.showerror", error)
    click(auth, "Test Connection")
    assert error.call_args.args[0] == "Missing Credentials"

    values = {"sess": "offline-session", "auth_id": "offline-id",
              "x_bc": "offline-bc", "user_agent": "offline-user-agent"}
    for key, value in values.items():
        getattr(auth, key + "_entry").insert(0, value)

    monkeypatch.setattr(OnlyFansAuth, "get_dynamic_rules", lambda self: {
        "static_param": "offline", "app_token": "test", "checksum_indexes": [1],
        "checksum_constant": 0, "format": "{hash}:{checksum}"
    })
    request = Mock(return_value=Mock(status_code=200))
    monkeypatch.setattr(browser_requests.Session, "request", request)
    click(auth, "Test Connection")
    assert request.call_args.kwargs["url"].endswith("/api2/v2/users/me")
    assert request.call_args.kwargs["cookies"]["sess"] == values["sess"]
    assert request.call_args.kwargs["headers"]["x-bc"] == values["x_bc"]
    info.assert_called_once()
    request.side_effect = requests.HTTPError("synthetic-secret-must-not-appear", response=Mock(status_code=401))
    click(auth, "Test Connection")
    assert "401" in error.call_args.args[1]
    assert "synthetic-secret-must-not-appear" not in error.call_args.args[1]

    creator = app.of_sections["creator"]
    creator.username_entry.insert(0, "offline-creator")
    creator.add_creator()
    start = Mock()
    monkeypatch.setattr(app.of_handlers.download_manager, "start", start)
    app.of_sections["buttons"]["start"].invoke()
    start.assert_called_once_with(app.of_app_state.config)
    assert app.of_app_state.config.user_names == {"offline-creator"}

    app.of_sections["settings"].auto_update_var.set(False)
    app.of_sections["settings"].rate_limit_slider.set(1.5)
    app.of_sections["settings"].incremental_var.set(True)
    auth.auth_uid_entry.insert(0, "offline-last-edit")
    app.on_close()
    restarted = launch()
    assert restarted.tab_view.get() == "OnlyFans"
    auth = restarted.of_sections["auth"]
    assert all(getattr(auth, k + "_entry").get() == v for k, v in values.items())
    assert auth.auth_uid_entry.get() == "offline-last-edit"
    assert restarted.of_sections["settings"].incremental_var.get()
    assert not restarted.of_sections["settings"].auto_update_var.get()
    assert restarted.of_sections["settings"].rate_limit_slider.get() == 1.5
    assert restarted.of_sections["creator"].get_selected_creators() == ["offline-creator"]
    assert not Path("config.ini").exists()


def test_fansly_setup_and_existing_profile(launch, monkeypatch):
    path = Path("config.ini")
    path.write_text("[Custom]\nkeep=yes\n[TargetedCreator]\nusername=existing\n"
                    "[Options]\nauto_check_updates=False\n", encoding="utf-8")
    app = launch()
    app.tab_view.set("Fansly")
    token = "offline-token-" * 5
    ua = "offline-user-agent-" * 3
    monkeypatch.setattr("utils.web.guess_check_key", Mock(return_value="offline-key"))
    api = Mock()
    api.return_value.device_id_timestamp = 123
    monkeypatch.setattr("api.FanslyApi", api)

    def fill_wizard(wizard):
        click(wizard.pages[0], "Next")
        wizard.token_entry.insert(0, token)
        click(wizard.pages[1], "Next")
        wizard.ua_entry.insert(0, ua)
        click(wizard.pages[2], "Next")
        click(wizard.pages[3], "Finish")

        def finish_when_saved():
            if wizard.current_page == 5:
                click(wizard.pages[5], "Done")
            else:
                app.after(50, finish_when_saved)
        finish_when_saved()
        wait_window(wizard)

    wait_window = app.wait_window
    monkeypatch.setattr(app, "wait_window", fill_wizard)

    def configure():
        click(app.sections["auth"], "Set Up Fansly...")
        app.quit()

    # A real mainloop allows the wizard's worker to post Tk callbacks.
    app.after_idle(configure)
    timeout = app.after(10000, app.destroy)
    app.mainloop()
    app.after_cancel(timeout)
    account = app.app_state.config
    assert account.token == token and account.user_agent == ua
    assert app.sections["auth"].token_entry.get() == token
    assert account.user_names == {"existing"}
    account.get_api()
    assert api.call_args.kwargs["token"] == token
    parser = ConfigParser()
    parser.read(path, encoding="utf-8")
    assert parser["Custom"]["keep"] == "yes"
    assert not parser.getboolean("Options", "auto_check_updates")
    app.on_close()
    restarted = launch()
    assert restarted.tab_view.get() == "Fansly"
    assert restarted.sections["auth"].token_entry.get() == token


def test_onlyfans_timeline_download_and_skip_existing(tmp_path, monkeypatch):
    from config.onlyfans_config import OnlyFansConfig
    from gui.download_runner import run_onlyfans_download

    api = Mock()
    api.get_user_by_username.return_value = {"id": 1, "username": "fixture"}
    url = "https://example.invalid/photo.jpg"
    api.get_timeline.return_value = {"list": [{
        "id": 10, "media": [{"id": 1, "type": "photo", "source": {"url": url}}]
    }]}
    payload = Mock()
    payload.iter_content.return_value = [b"offline media fixture"]
    fetch = Mock(return_value=payload)
    monkeypatch.setattr(requests, "get", fetch)
    monkeypatch.setattr("textio.textio._gui_config", None)
    config = OnlyFansConfig("1.0.0", user_names={"fixture"}, download_directory=tmp_path)
    monkeypatch.setattr(config, "get_api", lambda: api)
    for _ in range(2):
        assert run_onlyfans_download(config, Event(), Mock(), Mock())
    assert (tmp_path / "fixture-of/Timeline/10_1.jpg").read_bytes() == b"offline media fixture"
    fetch.assert_called_once_with(url, stream=True, timeout=60)
