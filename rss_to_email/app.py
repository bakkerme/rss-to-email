from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from rss_to_email.config import load_config
from rss_to_email.email_render import render_email
from rss_to_email.feeds import FeedItem, fetch_new_items
from rss_to_email.smtp_send import send_email
from rss_to_email.state import State, load_state, save_state


@dataclass(frozen=True)
class RunResult:
    new_items: list[FeedItem]
    failures: list[str]
    state: State
    run_started_at: datetime


def run_once(*, feed_list_path: str, state_path: str) -> None:
    config = load_config(feed_list_path=feed_list_path, state_path=state_path)

    run_started_at = datetime.now(timezone.utc)
    prior_state = load_state(config.state_path)

    new_items, failures, next_state = fetch_new_items(
        feed_urls=config.feed_urls,
        prior_state=prior_state,
        run_started_at=run_started_at,
        config=config,
    )

    if prior_state.last_run_utc is None and not config.initial_run_send:
        logging.info(
            "Initial run: warm-starting (mark seen, set last_run, send nothing)."
        )
        next_state.last_run_utc = run_started_at
        save_state(config.state_path, next_state)
        return

    if not new_items:
        logging.info("No new items.")
        if not failures:
            next_state.last_run_utc = run_started_at
            save_state(config.state_path, next_state)
        else:
            save_state(config.state_path, next_state)
            logging.warning(
                "Feed failures occurred; not advancing last_run: %s", failures
            )
        return

    subject, text_body, html_body = render_email(
        items=new_items,
        failures=failures,
        now_utc=run_started_at,
        subject_prefix=config.mail_subject_prefix,
    )

    send_email(
        smtp_config=config.smtp,
        subject=subject,
        text_body=text_body,
        html_body=html_body,
    )

    if failures:
        save_state(config.state_path, next_state)
        logging.warning(
            "Email sent, but not advancing last_run due to feed failures."
        )
        return

    next_state.last_run_utc = run_started_at
    save_state(config.state_path, next_state)
    logging.info("Sent %d new items.", len(new_items))
