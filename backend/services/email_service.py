import smtplib
from email.message import EmailMessage

from config import get_settings


def send_email(to_address: str, subject: str, body: str) -> None:
    settings = get_settings()
    if not settings.SMTP_HOST or not settings.SMTP_FROM:
        raise RuntimeError("SMTP is not configured")

    message = EmailMessage()
    message["From"] = settings.SMTP_FROM
    message["To"] = to_address
    message["Subject"] = subject
    message.set_content(body)

    if settings.SMTP_USE_SSL:
        server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT)
    else:
        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
        if settings.SMTP_USE_TLS:
            server.starttls()

    try:
        if settings.SMTP_USERNAME:
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.send_message(message)
    finally:
        server.quit()
