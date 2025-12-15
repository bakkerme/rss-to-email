from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class FeedState:
    seen_uids: list[str]


@dataclass
class State:
    last_run_utc: datetime | None
    feeds: dict[str, FeedState]

    def copy(self) -> "State":
        return State(
            last_run_utc=self.last_run_utc,
            feeds={k: FeedState(seen_uids=list(v.seen_uids)) for k, v in self.feeds.items()},
        )


def _dt_to_str(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _dt_from_str(s: str) -> datetime:
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s).astimezone(timezone.utc)


def load_state(path: str) -> State:
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except FileNotFoundError:
        return State(last_run_utc=None, feeds={})

    last_run = raw.get("last_run_utc")
    feeds_raw = raw.get("feeds", {}) or {}
    feeds: dict[str, FeedState] = {}
    for feed_url, fs in feeds_raw.items():
        seen_uids = list((fs or {}).get("seen_uids", []) or [])
        feeds[str(feed_url)] = FeedState(seen_uids=seen_uids)

    return State(last_run_utc=_dt_from_str(last_run) if last_run else None, feeds=feeds)


def save_state(path: str, state: State) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp_path = f"{path}.tmp"

    raw = {
        "last_run_utc": _dt_to_str(state.last_run_utc) if state.last_run_utc else None,
        "feeds": {k: {"seen_uids": v.seen_uids} for k, v in state.feeds.items()},
    }
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(raw, f, indent=2, sort_keys=True)
        f.write("\n")
    os.replace(tmp_path, path)
