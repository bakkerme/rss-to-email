from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlparse

import feedparser
import requests

from rss_to_email.config import Config
from rss_to_email.state import FeedState, State
from rss_to_email.util import coerce_uid, datetime_from_struct_time, safe_get


@dataclass(frozen=True)
class FeedItem:
    feed_url: str
    feed_domain: str
    feed_title: str | None
    entry_uid: str
    entry_title: str | None
    entry_link: str | None
    published_utc: datetime | None


def _fetch_feed(*, url: str, config: Config) -> feedparser.FeedParserDict:
    headers = {"User-Agent": config.user_agent}
    resp = requests.get(url, headers=headers, timeout=config.http_timeout_seconds)
    resp.raise_for_status()
    return feedparser.parse(resp.content)


def _format_failure(*, url: str, exc: Exception, user_agent: str) -> str:
    details: list[str] = [exc.__class__.__name__]
    message = str(exc)
    if message:
        details.append(message)

    if isinstance(exc, requests.HTTPError) and exc.response is not None:
        response = exc.response
        status = f"{response.status_code} {response.reason}".strip()
        if status:
            details.append(f"status={status}")
        header_keys = {
            "content-type",
            "retry-after",
            "server",
            "x-cache",
            "x-request-id",
        }
        headers = {
            key: value
            for key, value in response.headers.items()
            if key.lower() in header_keys
        }
        if headers:
            header_summary = ", ".join(f"{key}={value}" for key, value in headers.items())
            details.append(f"headers={header_summary}")
    elif isinstance(exc, requests.RequestException):
        request = getattr(exc, "request", None)
        method = getattr(request, "method", None) if request is not None else None
        request_url = getattr(request, "url", None) if request is not None else None
        if method and request_url:
            details.append(f"request={method} {request_url}")

    details.append(f"ua={user_agent}")
    return f"{url} ({'; '.join(details)})"


def fetch_new_items(
    *,
    feed_urls: list[str],
    prior_state: State,
    run_started_at: datetime,
    config: Config,
) -> tuple[list[FeedItem], list[str], State]:
    new_items: list[FeedItem] = []
    failures: list[str] = []

    next_state = prior_state.copy()
    last_run = prior_state.last_run_utc
    warm_start = last_run is None and not config.initial_run_send

    for feed_url in feed_urls:
        parsed_domain = urlparse(feed_url).netloc or feed_url
        feed_state = next_state.feeds.get(feed_url) or FeedState(seen_uids=[])
        seen = set(feed_state.seen_uids)

        try:
            parsed = _fetch_feed(url=feed_url, config=config)
        except Exception as exc:
            failure = _format_failure(url=feed_url, exc=exc, user_agent=config.user_agent)
            failures.append(failure)
            logging.warning("Failed to fetch %s: %s", feed_url, failure)
            next_state.feeds[feed_url] = feed_state
            continue

        feed_title = safe_get(parsed, "feed", "title")
        entries = list(parsed.entries or [])
        if config.max_items_per_feed is not None:
            entries = entries[: config.max_items_per_feed]

        uids_to_mark_seen: list[tuple[datetime | None, str]] = []

        for entry in entries:
            entry_uid = coerce_uid(entry)
            if not entry_uid:
                continue
            if entry_uid in seen:
                continue

            published = datetime_from_struct_time(
                entry.get("published_parsed") or entry.get("updated_parsed")
            )
            if published is not None:
                published = published.astimezone(timezone.utc)

            if not warm_start:
                if last_run is not None and published is not None and published <= last_run:
                    continue

                new_items.append(
                    FeedItem(
                        feed_url=feed_url,
                        feed_domain=parsed_domain,
                        feed_title=feed_title,
                        entry_uid=entry_uid,
                        entry_title=safe_get(entry, "title"),
                        entry_link=safe_get(entry, "link"),
                        published_utc=published,
                    )
                )

            uids_to_mark_seen.append((published, entry_uid))

        if warm_start:
            uids_to_mark_seen = []
            for entry in reversed(entries):
                entry_uid = coerce_uid(entry)
                if entry_uid:
                    uids_to_mark_seen.append((None, entry_uid))

        if uids_to_mark_seen:
            uids_to_mark_seen.sort(key=lambda x: (x[0] is None, x[0] or run_started_at))
            feed_state.seen_uids.extend([uid for _published, uid in uids_to_mark_seen])
            if config.seen_uids_per_feed_limit > 0:
                feed_state.seen_uids = feed_state.seen_uids[
                    -config.seen_uids_per_feed_limit :
                ]

        next_state.feeds[feed_url] = feed_state

    new_items.sort(key=lambda item: (item.feed_domain, item.published_utc or run_started_at))
    return new_items, failures, next_state
