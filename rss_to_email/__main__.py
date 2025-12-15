from __future__ import annotations

import argparse
import logging
import os
import sys

from rss_to_email.app import run_once


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rss-to-email")
    parser.add_argument(
        "--feed-list",
        default=os.environ.get("FEED_LIST_PATH"),
        help="Path to plaintext file of feed URLs (or env FEED_LIST_PATH).",
    )
    parser.add_argument(
        "--state-path",
        default=os.environ.get("STATE_PATH") or os.environ.get("SQLITE_PATH"),
        help="Path to JSON state file (or env STATE_PATH).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(message)s",
    )

    if not args.feed_list:
        logging.error("Missing feed list path; set --feed-list or FEED_LIST_PATH.")
        return 2
    if not args.state_path:
        logging.error("Missing state path; set --state-path or STATE_PATH.")
        return 2

    try:
        run_once(feed_list_path=args.feed_list, state_path=args.state_path)
    except KeyboardInterrupt:
        return 130
    except Exception:
        logging.exception("Run failed.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
