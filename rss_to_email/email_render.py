from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from html import escape

from rss_to_email.feeds import FeedItem


def _fmt_dt(dt: datetime | None) -> str:
    if dt is None:
        return ""
    return dt.strftime("%Y-%m-%d %H:%M UTC")


def render_email(
    *,
    items: list[FeedItem],
    failures: list[str],
    now_utc: datetime,
    subject_prefix: str,
) -> tuple[str, str, str]:
    by_domain: dict[str, list[FeedItem]] = defaultdict(list)
    for item in items:
        by_domain[item.feed_domain].append(item)

    total = len(items)
    subject = f"{subject_prefix} ({total} new)"

    text_lines: list[str] = [f"{subject_prefix} - {total} new", ""]
    html_parts: list[str] = [
        "<!doctype html>",
        "<html>",
        "<head>",
        '<meta charset="utf-8"/>',
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"/>",
        "<title>" + escape(subject) + "</title>",
        "</head>",
        '<body style="font-family: -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif; line-height: 1.4;">',
        f"<h1 style=\"margin:0 0 8px 0;\">{escape(subject_prefix)}</h1>",
        f"<div style=\"color:#555; margin:0 0 16px 0;\">{escape(_fmt_dt(now_utc))} • {total} new</div>",
    ]

    for domain in sorted(by_domain.keys()):
        domain_items = by_domain[domain]
        text_lines.append(domain)
        html_parts.append(f"<h2 style=\"margin:20px 0 8px 0;\">{escape(domain)}</h2>")
        html_parts.append("<ol style=\"margin:0; padding-left: 22px;\">")
        for item in domain_items:
            title = item.entry_title or item.entry_link or item.entry_uid
            link = item.entry_link or ""
            published = _fmt_dt(item.published_utc)

            text_lines.append(f"- {title}")
            if link:
                text_lines.append(f"  {link}")
            if published:
                text_lines.append(f"  {published}")

            safe_title = escape(title)
            safe_link = escape(link)
            meta = " • ".join(x for x in [escape(item.feed_title or ""), escape(published)] if x)
            meta_html = f'<div style="color:#666; font-size: 12px; margin-top: 2px;">{meta}</div>' if meta else ""
            link_html = (
                f'<a href="{safe_link}" style="color:#0b57d0; text-decoration:none;">{safe_title}</a>'
                if link
                else safe_title
            )
            html_parts.append(f"<li style=\"margin: 8px 0;\">{link_html}{meta_html}</li>")
        html_parts.append("</ol>")
        text_lines.append("")

    if failures:
        text_lines.append("Failures:")
        for failure in failures:
            text_lines.append(f"- {failure}")

        html_parts.append("<h2 style=\"margin:20px 0 8px 0;\">Failures</h2>")
        html_parts.append("<ul style=\"margin:0; padding-left: 18px; color:#a00;\">")
        for failure in failures:
            html_parts.append(f"<li>{escape(failure)}</li>")
        html_parts.append("</ul>")

    html_parts.append("</body></html>")
    text_body = "\n".join(text_lines).rstrip() + "\n"
    html_body = "\n".join(html_parts) + "\n"
    return subject, text_body, html_body
