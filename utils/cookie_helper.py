"""Parse explicit Cookie Helper exports locally; never log input or contact a server.

OnlyGoblins modifications, ZenoBell, 2026-11-06. GPL-3.0.
"""

import json
import re

MAX_EXPORT_BYTES = 65536
FIELDS = ("sess", "auth_id", "auth_uid", "user_agent", "x_bc")


class CookieHelperError(ValueError):
    """A safe, fixed diagnostic which never contains user-supplied values."""


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise CookieHelperError("Duplicate JSON fields are not supported.")
        result[key] = value
    return result


def _value(value, label, optional=False):
    if optional and value in (None, ""):
        return ""
    if (not isinstance(value, str) or not value.strip() or len(value) > 8192
            or any(ord(c) < 32 or ord(c) == 127 or 0xD800 <= ord(c) <= 0xDFFF for c in value)):
        raise CookieHelperError(f"Missing or invalid {label}.")
    return value.strip()


def parse_cookie_helper_export(raw):
    """Return only existing desktop fields, without changing any config.

    Accept the upstream {auth: {...}} format and its unwrapped auth object.
    Cookie names are parsed exactly; auth_uid must match the exported auth_id.
    Unknown upstream metadata is ignored, never copied into configuration.
    """
    if not isinstance(raw, str) or len(raw.encode("utf-8", errors="replace")) > MAX_EXPORT_BYTES:
        raise CookieHelperError("Export is too large (maximum 64 KiB).")
    try:
        data = json.loads(raw.lstrip("\ufeff"), object_pairs_hook=_unique_object)
    except (ValueError, RecursionError):
        raise CookieHelperError("Invalid JSON. Paste a complete Cookie Helper export.") from None
    if not isinstance(data, dict):
        raise CookieHelperError("Expected an authentication JSON object.")
    auth = data.get("auth", data)
    if not isinstance(auth, dict):
        raise CookieHelperError("Expected an auth object.")
    cookie = _value(auth.get("cookie"), "cookie string")
    values = {}
    for part in cookie.split(";"):
        if not part.strip():
            continue
        name, separator, value = part.strip().partition("=")
        if not separator or not re.fullmatch(r"[A-Za-z0-9_\-]+", name) or name in values:
            raise CookieHelperError("Malformed or duplicate cookie fields.")
        values[name] = value
    auth_id = _value(values.get("auth_id"), "auth_id")
    if not re.fullmatch(r"[0-9]+", auth_id):
        raise CookieHelperError("auth_id must contain digits only.")
    if any(name.startswith("auth_uid_") and name != f"auth_uid_{auth_id}" for name in values):
        raise CookieHelperError("Auth UID belongs to a different account. Export again.")
    return {
        "sess": _value(values.get("sess"), "sess"),
        "auth_id": auth_id,
        "auth_uid": _value(values.get(f"auth_uid_{auth_id}"), "auth_uid", optional=True),
        "user_agent": _value(auth.get("user_agent"), "user_agent"),
        "x_bc": _value(auth.get("x_bc"), "x_bc"),
    }
