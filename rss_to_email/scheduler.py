from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone

from croniter import croniter

from rss_to_email.app import run_once


@dataclass(frozen=True)
class CronConfig:
    schedule: str
    immediate: bool
    max_sleep_seconds: float


def run_on_schedule(
    *,
    feed_list_path: str,
    state_path: str,
    cron_config: CronConfig,
) -> None:
    schedule = cron_config.schedule.strip()
    if not schedule:
        raise ValueError("CRON_SCHEDULE is empty.")

    logging.info("Scheduler enabled with CRON_SCHEDULE=%r (UTC).", schedule)

    if cron_config.immediate:
        logging.info("CRON_IMMEDIATE=true: running once at startup.")
        run_once(feed_list_path=feed_list_path, state_path=state_path)

    while True:
        now = datetime.now(timezone.utc)
        itr = croniter(schedule, now)
        next_dt = itr.get_next(datetime)

        sleep_seconds = max(0.0, (next_dt - now).total_seconds())
        logging.info("Next run at %s (in %.1fs).", next_dt.isoformat(), sleep_seconds)

        remaining = sleep_seconds
        while remaining > 0:
            chunk = min(remaining, cron_config.max_sleep_seconds)
            time.sleep(chunk)
            remaining -= chunk

        run_once(feed_list_path=feed_list_path, state_path=state_path)
