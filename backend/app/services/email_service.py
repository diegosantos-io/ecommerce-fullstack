import smtplib
from email.message import EmailMessage

from app.database.database import settings


def send_email(
    to_email: str,
    subject: str,
    body: str,
) -> None:
    message = EmailMessage()

    message["From"] = settings.EMAIL_FROM
    message["To"] = to_email
    message["Subject"] = subject

    message.set_content(body)

    with smtplib.SMTP(
        settings.EMAIL_HOST,
        settings.EMAIL_PORT,
        timeout=30,
    ) as server:
        server.starttls()

        server.login(
            settings.EMAIL_USERNAME,
            settings.EMAIL_PASSWORD,
        )

        server.send_message(message)