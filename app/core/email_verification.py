from itsdangerous import URLSafeTimedSerializer

from app.core.config import settings


serializer = URLSafeTimedSerializer(
    settings.JWT_SECRET_KEY,
    salt="user-email-verification-v1",
)


def create_verification_token(user_id: int, email: str) -> str:
    return serializer.dumps(
        {"user_id": user_id, "email": email}
    )


def verify_email_token(token: str) -> dict:
    return serializer.loads(token, max_age=86400)
