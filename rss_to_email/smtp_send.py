from __future__ import annotations

import smtplib
from email.message import EmailMessage

from rss_to_email.config import SmtpConfig


def send_email(
    *,
    smtp_config: SmtpConfig,
    subject: str,
    text_body: str,
    html_body: str,
) -> None:
    msg = EmailMessage()
    msg["From"] = smtp_config.mail_from
    msg["To"] = smtp_config.mail_to
    msg["Subject"] = subject
    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype="html")

    if smtp_config.use_ssl:
        with smtplib.SMTP_SSL(smtp_config.host, smtp_config.port) as server:
            server.login(smtp_config.username, smtp_config.password)
            server.send_message(msg)
        return

    with smtplib.SMTP(smtp_config.host, smtp_config.port) as server:
        server.ehlo()
        if smtp_config.use_tls:
            server.starttls()
            server.ehlo()
        server.login(smtp_config.username, smtp_config.password)
        server.send_message(msg)
