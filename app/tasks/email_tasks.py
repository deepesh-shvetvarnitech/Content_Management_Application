import smtplib
from email.message import EmailMessage

from app.core.celery_app import celery_app
from app.core.config import settings
from app.core.email_verification import create_verification_token


@celery_app.task(
    name="app.tasks.email_tasks.send_verification_email",
    autoretry_for=(OSError, smtplib.SMTPException),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def send_verification_email(
    user_id: int,
    email: str,
    name: str,
) -> dict:
    required = (
        settings.SMTP_HOST,
        settings.SMTP_FROM_EMAIL,
        settings.SMTP_USERNAME,
        settings.SMTP_PASSWORD,
    )
    if not all(required):
        raise RuntimeError(
            "SMTP configuration is incomplete. Configure SMTP in .env."
        )

    token = create_verification_token(user_id, email)
    link = f"{settings.EMAIL_VERIFICATION_BASE_URL}?token={token}"

    message = EmailMessage()
    message["Subject"] = "Verify your email address"
    message["From"] = settings.SMTP_FROM_EMAIL
    message["To"] = email
    message.set_content(
        f"Hello {name},\n\n"
        f"Please verify your email using this link:\n{link}\n\n"
        "This link expires in 24 hours.\n"
        "If you did not create this account, ignore this email."
    )

    with smtplib.SMTP(
        settings.SMTP_HOST,
        settings.SMTP_PORT,
        timeout=20,
    ) as server:
        server.ehlo()
        if settings.SMTP_USE_TLS:
            server.starttls()
            server.ehlo()

        server.login(
            settings.SMTP_USERNAME,
            settings.SMTP_PASSWORD,
        )
        server.send_message(message)

    return {"status": "sent", "email": email}
