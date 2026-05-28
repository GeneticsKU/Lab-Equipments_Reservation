from __future__ import annotations

from email.message import EmailMessage
import smtplib

from bridge.config import BridgeSettings


def _build_email_message(settings: BridgeSettings, *, to_email: str, subject: str, html: str, text: str) -> EmailMessage:
    message = EmailMessage()
    message["From"] = settings.smtp_from_email
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(text)
    message.add_alternative(html, subtype="html")
    return message


def _send_email(settings: BridgeSettings, *, to_email: str, subject: str, html: str, text: str):
    message = _build_email_message(
        settings,
        to_email=to_email,
        subject=subject,
        html=html,
        text=text,
    )
    smtp_client_type = smtplib.SMTP_SSL if settings.smtp_use_ssl else smtplib.SMTP
    with smtp_client_type(settings.smtp_host, settings.smtp_port) as smtp_client:
        if not settings.smtp_use_ssl:
            smtp_client.starttls()
        smtp_client.login(settings.smtp_username, settings.smtp_password)
        smtp_client.send_message(message)
    return {"status": "sent", "to": to_email, "subject": subject}


def send_login_code_email(settings: BridgeSettings, to_email: str, login_code: str):
    subject = "Genetics Lab login code"
    html = (
        "<p>Your Genetics Lab Equipment Reservation login code is "
        f"<strong>{login_code}</strong>.</p>"
        "<p>The code expires soon. If you did not request it, you can ignore this email.</p>"
    )
    text = (
        "Your Genetics Lab Equipment Reservation login code is "
        f"{login_code}. The code expires soon."
    )
    return _send_email(settings, to_email=to_email, subject=subject, html=html, text=text)


def send_sponsor_approval_email(settings: BridgeSettings, to_email: str, request_id: str):
    approval_link = f"{settings.app_base_url}?approve_request={request_id}"
    subject = "Approval requested for Genetics Lab access"
    html = (
        "<p>A KU user has requested access to the Genetics Lab Equipment Reservation app.</p>"
        f"<p>Review the request here: <a href=\"{approval_link}\">{approval_link}</a></p>"
    )
    text = (
        "A KU user has requested access to the Genetics Lab Equipment Reservation app. "
        f"Review the request here: {approval_link}"
    )
    return _send_email(settings, to_email=to_email, subject=subject, html=html, text=text)
