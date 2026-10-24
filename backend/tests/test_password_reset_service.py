
import hashlib
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from app.models import User
from app.models.password_reset_token import PasswordResetToken
from app.services.password_reset_service import (
    create_password_reset_token,
    reset_user_password,
)
from app.utils.password import verify_password


def make_user():
    return User(
        id=10,
        nome="Cliente Teste",
        email="cliente.teste@example.com",
        senha_hash="hash-antigo",
        role="cliente",
        ativo=True,
    )


def make_reset_token(raw_token, user_id=10, expired=False, used=False):
    now = datetime.now(timezone.utc)
    token_hash = hashlib.sha256(
        raw_token.encode("utf-8")
    ).hexdigest()

    return PasswordResetToken(
        id=1,
        user_id=user_id,
        token_hash=token_hash,
        expires_at=(
            now - timedelta(minutes=1)
            if expired
            else now + timedelta(minutes=30)
        ),
        used_at=now if used else None,
    )


def test_reset_rejects_expired_token():
    raw_token = "token-de-teste-expirado"
    reset_token = make_reset_token(raw_token, expired=True)

    fake_db = MagicMock()
    fake_db.query.return_value.filter.return_value.first.return_value = reset_token

    result = reset_user_password(
        fake_db,
        raw_token,
        "NovaSenha123",
    )

    assert result is False
    fake_db.commit.assert_not_called()


def test_reset_rejects_already_used_token():
    raw_token = "token-de-teste-ja-usado"
    reset_token = make_reset_token(raw_token, used=True)

    fake_db = MagicMock()
    fake_db.query.return_value.filter.return_value.first.return_value = reset_token

    result = reset_user_password(
        fake_db,
        raw_token,
        "NovaSenha123",
    )

    assert result is False
    fake_db.commit.assert_not_called()


def test_reset_updates_password_hash_and_consumes_token():
    raw_token = "token-de-teste-valido"
    reset_token = make_reset_token(raw_token)
    user = make_user()

    fake_db = MagicMock()
    query = fake_db.query.return_value
    query.filter.return_value.first.side_effect = [
        reset_token,
        user,
    ]

    result = reset_user_password(
        fake_db,
        raw_token,
        "NovaSenha123",
    )

    assert result is True
    assert verify_password("NovaSenha123", user.senha_hash)
    assert not verify_password("SenhaAntiga123", user.senha_hash)
    assert reset_token.used_at is not None
    fake_db.commit.assert_called_once()


def test_reset_rejects_inactive_user():
    raw_token = "token-de-usuario-inativo"
    reset_token = make_reset_token(raw_token)
    user = make_user()
    user.ativo = False

    fake_db = MagicMock()
    query = fake_db.query.return_value
    query.filter.return_value.first.side_effect = [
        reset_token,
        user,
    ]

    result = reset_user_password(
        fake_db,
        raw_token,
        "NovaSenha123",
    )

    assert result is False
    fake_db.commit.assert_not_called()


@patch("app.services.password_reset_service.secrets.token_urlsafe")
def test_create_token_stores_only_hash(mock_token_urlsafe):
    raw_token = "token-original-secreto"
    mock_token_urlsafe.return_value = raw_token

    user = make_user()
    fake_db = MagicMock()
    fake_db.query.return_value.filter.return_value.all.return_value = []

    returned_token = create_password_reset_token(fake_db, user)

    assert returned_token == raw_token

    added_token = fake_db.add.call_args.args[0]
    expected_hash = hashlib.sha256(
        raw_token.encode("utf-8")
    ).hexdigest()

    assert isinstance(added_token, PasswordResetToken)
    assert added_token.token_hash == expected_hash
    assert added_token.token_hash != raw_token
    assert added_token.expires_at > datetime.now(timezone.utc)
    fake_db.commit.assert_called_once()
