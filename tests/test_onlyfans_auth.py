"""OnlyFans request construction, without account traffic."""
from unittest.mock import Mock

import pytest

from api.onlyfans_auth import OnlyFansAuth


@pytest.mark.parametrize("uid", [None, "", "offline-uid"])
def test_cookies_preserve_supplied_values_and_do_not_invent_uid(uid):
    auth = OnlyFansAuth("offline-session", "123", uid, "offline-agent", "offline-bc")
    expected = {"sess": "offline-session", "auth_id": "123"}
    if uid:
        expected["auth_uid_123"] = uid
    assert auth.get_cookies() == expected


@pytest.mark.parametrize("removed", [[], ["user-id"], ["USER-ID", "referer"]])
def test_request_headers_follow_rule_provider_removals(removed):
    auth = OnlyFansAuth("offline-session", "123", None, "offline-agent", "offline-bc")
    auth.get_dynamic_rules = Mock(return_value={
        "static_param": "offline", "format": "test:{}:{:x}:end",
        "checksum_indexes": [0, 1], "checksum_constant": 2,
        "app_token": "offline-app", "remove_headers": removed,
    })
    headers = auth.get_headers("https://onlyfans.com/api2/v2/users/me")
    assert headers["sign"].startswith("test:")
    assert headers["x-bc"] == "offline-bc"
    assert ("user-id" in headers) == ("user-id" not in [name.lower() for name in removed])
    for name in removed:
        assert name.lower() not in headers


def test_current_rule_provider_format_is_normalized(monkeypatch):
    import requests
    response = Mock(status_code=200)
    response.json.return_value = {
        "prefix": "test", "suffix": "end", "app-token": "app",
        "static_param": "fixture", "checksum_indexes": [0], "checksum_constant": 1,
    }
    monkeypatch.setattr(requests, "get", Mock(return_value=response))
    auth = OnlyFansAuth("fixture", "123", None, "agent", "bc")
    rules = auth.get_dynamic_rules()
    assert rules["app_token"] == "app"
    assert rules["format"] == "test:{}:{:x}:end"
    assert auth.get_headers("https://onlyfans.com/api2/v2/users/me")["sign"].startswith("test:")


def test_api_preserves_http_error_response(monkeypatch):
    import requests
    from api.onlyfans_api import OnlyFansApi
    api = OnlyFansApi("fixture", "123", None, "Firefox", "bc")
    monkeypatch.setattr(api.auth, "get_headers", lambda url: {})
    response = Mock(status_code=403, reason="Forbidden")
    monkeypatch.setattr(api.session, "request", Mock(return_value=response))
    with pytest.raises(requests.HTTPError) as raised:
        api.test_auth()
    assert raised.value.response is response
    api.session.close()
