from __future__ import annotations

from bridge.config import BridgeSettings
from bridge.emailer import send_login_code_email, send_sponsor_approval_email


class FakeSmtpClient:
    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self.started_tls = False
        self.login_args = None
        self.sent_message = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def starttls(self) -> None:
        self.started_tls = True

    def login(self, username: str, password: str) -> None:
        self.login_args = (username, password)

    def send_message(self, message) -> None:
        self.sent_message = message


def build_settings(*, smtp_use_ssl: bool) -> BridgeSettings:
    return BridgeSettings(
        database_url="postgresql://example",
        smtp_host="smtp.gmail.com",
        smtp_port=465 if smtp_use_ssl else 587,
        smtp_username="sender@gmail.com",
        smtp_password="app-password",
        smtp_from_email="sender@gmail.com",
        smtp_use_ssl=smtp_use_ssl,
        app_base_url="https://example.streamlit.app",
    )


def test_send_login_code_email_uses_ssl_smtp(monkeypatch) -> None:
    settings = build_settings(smtp_use_ssl=True)
    fake_client = FakeSmtpClient(settings.smtp_host, settings.smtp_port)

    monkeypatch.setattr("bridge.emailer.smtplib.SMTP_SSL", lambda host, port: fake_client)

    result = send_login_code_email(settings, "student@ku.th", "123456")

    assert result["status"] == "sent"
    assert fake_client.login_args == (settings.smtp_username, settings.smtp_password)
    assert fake_client.sent_message["To"] == "student@ku.th"
    assert fake_client.sent_message["Subject"] == "Genetics Lab login code"
    assert "123456" in fake_client.sent_message.as_string()
    assert fake_client.started_tls is False


def test_send_sponsor_approval_email_uses_starttls_when_ssl_disabled(monkeypatch) -> None:
    settings = build_settings(smtp_use_ssl=False)
    fake_client = FakeSmtpClient(settings.smtp_host, settings.smtp_port)

    monkeypatch.setattr("bridge.emailer.smtplib.SMTP", lambda host, port: fake_client)

    result = send_sponsor_approval_email(settings, "lecturer@ku.th", "request-123")

    assert result["status"] == "sent"
    assert fake_client.started_tls is True
    assert fake_client.login_args == (settings.smtp_username, settings.smtp_password)
    assert fake_client.sent_message["To"] == "lecturer@ku.th"
    plain_text_body = fake_client.sent_message.get_body(preferencelist=("plain",))
    assert plain_text_body is not None
    assert "approve_request=request-123" in plain_text_body.get_content()
