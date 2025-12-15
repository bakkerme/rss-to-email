from __future__ import annotations

import calendar
from datetime import datetime, timezone
from typing import Any


def parse_bool(value: str) -> bool:
    v = value.strip().lower()
    if v in {"1", "true", "yes", "y", "on"}:
        return True
    if v in {"0", "false", "no", "n", "off"}:
        return False
    raise ValueError(f"Invalid boolean value: {value!r}")


def read_feed_list(path: str) -> list[str]:
    urls: list[str] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            urls.append(stripped)
    return urls


def safe_get(obj: Any, *keys: str) -> Any:
    cur: Any = obj
    for key in keys:
        if cur is None:
            return None
        if isinstance(cur, dict):
            cur = cur.get(key)
        else:
            cur = getattr(cur, key, None)
    return cur


def coerce_uid(entry: Any) -> str | None:
    for key in ("id", "guid"):
        uid = safe_get(entry, key)
        if uid:
            return str(uid)
    link = safe_get(entry, "link")
    if link:
        return str(link)
    return None


def datetime_from_struct_time(st: Any) -> datetime | None:
    if st is None:
        return None
    try:
        ts = calendar.timegm(st)
    except Exception:
        return None
    return datetime.fromtimestamp(ts, tz=timezone.utc)
