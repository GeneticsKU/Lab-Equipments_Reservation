from __future__ import annotations

import resend

from bridge.config import BridgeSettings


def _send_email(settings: BridgeSettings, *, to_email: str, subject: str, html: str, text: str):
    resend.api_key = settings.resend_api_key
    payload = {
        "from": settings.resend_from_email,
        "to": [to_email],
        "subject": subject,
        "html": html,
        "text": text,
    }
    return resend.Emails.send(payload)


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

