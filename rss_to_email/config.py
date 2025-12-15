from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Final

from rss_to_email.util import parse_bool, read_feed_list


@dataclass(frozen=True)
class SmtpConfig:
    host: str
    port: int
    username: str
    password: str
    use_tls: bool
    use_ssl: bool
    mail_from: str
    mail_to: str


@dataclass(frozen=True)
class Config:
    feed_list_path: str
    state_path: str
    feed_urls: list[str]
    user_agent: str
    http_timeout_seconds: float
    max_items_per_feed: int | None
    seen_uids_per_feed_limit: int
    initial_run_send: bool
    mail_subject_prefix: str
    smtp: SmtpConfig


_DEFAULT_UA: Final[str] = "rss-to-email/0.1"


def load_config(*, feed_list_path: str, state_path: str) -> Config:
    feed_urls = read_feed_list(feed_list_path)
    if not feed_urls:
        raise ValueError(f"No feed URLs found in {feed_list_path!r}.")

    smtp_host = os.environ["SMTP_HOST"]
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_username = os.environ["SMTP_USERNAME"]
    smtp_password = os.environ["SMTP_PASSWORD"]
    smtp_from = os.environ["SMTP_FROM"]
    smtp_to = os.environ["SMTP_TO"]

    smtp_use_ssl = parse_bool(os.environ.get("SMTP_USE_SSL", "false"))
    smtp_use_tls = parse_bool(os.environ.get("SMTP_USE_TLS", "true"))
    if smtp_use_ssl and smtp_use_tls:
        raise ValueError("Only one of SMTP_USE_SSL and SMTP_USE_TLS can be true.")

    max_items_raw = os.environ.get("MAX_ITEMS_PER_FEED")
    max_items = int(max_items_raw) if max_items_raw else None

    return Config(
        feed_list_path=feed_list_path,
        state_path=state_path,
        feed_urls=feed_urls,
        user_agent=os.environ.get("USER_AGENT", _DEFAULT_UA),
        http_timeout_seconds=float(os.environ.get("HTTP_TIMEOUT_SECONDS", "20")),
        max_items_per_feed=max_items,
        seen_uids_per_feed_limit=int(os.environ.get("SEEN_UIDS_PER_FEED_LIMIT", "2000")),
        initial_run_send=parse_bool(os.environ.get("INITIAL_RUN_SEND", "false")),
        mail_subject_prefix=os.environ.get("MAIL_SUBJECT_PREFIX", "RSS updates"),
        smtp=SmtpConfig(
            host=smtp_host,
            port=smtp_port,
            username=smtp_username,
            password=smtp_password,
            use_tls=smtp_use_tls,
            use_ssl=smtp_use_ssl,
            mail_from=smtp_from,
            mail_to=smtp_to,
        ),
    )
