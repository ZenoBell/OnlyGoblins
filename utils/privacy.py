# FanGoblin modifications by ZenoBell, 2026-11-06. See CHANGES_FROM_UPSTREAM.md.
"""Redact session values and signed URL queries from diagnostic output."""

import re
from threading import Lock

_secrets = frozenset()
_lock = Lock()
_fields = re.compile(
    r"(?i)([\"']?(?:authorization(?:_token)?|token|sess|auth_id|auth_uid(?:_\d+)?|"
    r"auth_hash|auth_uniq(?:_\d+)?|x[_-]bc|cookie|password)[\"']?\s*[:=]\s*[\"']?)"
    r"([^\s\"'\\,;}]+)"
)
_urls = re.compile(r"(https?://[^\s\"'<>?]+)\?[^\s\"'<>]+")


def register_secrets(*values):
    global _secrets
    with _lock:
        _secrets = _secrets.union(value for value in values if isinstance(value, str) and value)


def redact_sensitive(message):
    text = str(message)
    for secret in sorted(_secrets, key=len, reverse=True):
        text = text.replace(secret, "[REDACTED]")
    text = _fields.sub(lambda match: match.group(1) + "[REDACTED]", text)
    return _urls.sub(r"\1?[REDACTED]", text)
