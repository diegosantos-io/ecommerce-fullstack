
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models import User
from app.models.password_reset_token import PasswordResetToken
from app.utils.password import hash_password


TOKEN_EXPIRATION_MINUTES = 30


def create_password_reset_token(
    db: Session,
    user: User,
) -> str:
    # Invalida tokens anteriores ainda não utilizados.
    now = datetime.now(timezone.utc)

    previous_tokens = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at.is_(None),
        )
        .all()
    )

    for previous_token in previous_tokens:
        previous_token.used_at = now

    # Gera um token aleatório e armazena somente seu hash.
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(
        raw_token.encode("utf-8")
    ).hexdigest()

    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=now + timedelta(
            minutes=TOKEN_EXPIRATION_MINUTES
        ),
    )

    db.add(reset_token)
    db.commit()

    # O token original será enviado por e-mail.
    return raw_token


def reset_user_password(
    db: Session,
    raw_token: str,
    new_password: str,
) -> bool:
    token_hash = hashlib.sha256(
        raw_token.encode("utf-8")
    ).hexdigest()

    reset_token = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.token_hash == token_hash
        )
        .first()
    )

    if not reset_token:
        return False

    now = datetime.now(timezone.utc)
    expires_at = reset_token.expires_at

    # Compatibilidade com timestamps que possam vir sem fuso.
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(
            tzinfo=timezone.utc
        )

    if reset_token.used_at is not None:
        return False

    if expires_at <= now:
        return False

    user = (
        db.query(User)
        .filter(User.id == reset_token.user_id)
        .first()
    )

    if not user or not user.ativo:
        return False

    user.senha_hash = hash_password(new_password)
    reset_token.used_at = now

    db.commit()

    return True
