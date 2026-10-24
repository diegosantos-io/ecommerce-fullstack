
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.database.database import get_db
from app.models import User
from app.models.password_reset_token import PasswordResetToken
from app.utils.password import hash_password


client = TestClient(app)


def make_user():
    return User(
        id=10,
        nome="Cliente Teste",
        email="cliente.teste@example.com",
        senha_hash=hash_password("SenhaAntiga123"),
        role="cliente",
        ativo=True,
    )


def test_request_reset_returns_generic_message_for_unknown_email():
    fake_db = MagicMock()
    fake_db.query.return_value.filter.return_value.first.return_value = None

    app.dependency_overrides[get_db] = lambda: fake_db

    try:
        response = client.post(
            "/usuarios/recuperar-senha",
            json={"email": "nao.existe@example.com"},
        )

        assert response.status_code == 200
        assert "Se o e-mail estiver cadastrado" in response.json()["message"]
    finally:
        app.dependency_overrides.clear()


def test_request_reset_sends_email_for_active_user():
    fake_db = MagicMock()
    user = make_user()
    fake_db.query.return_value.filter.return_value.first.return_value = user

    app.dependency_overrides[get_db] = lambda: fake_db

    with patch(
        "app.routers.password_reset.create_password_reset_token",
        return_value="token-de-teste-comprido-123456",
    ), patch(
        "app.routers.password_reset.send_email"
    ) as mock_send_email:
        try:
            response = client.post(
                "/usuarios/recuperar-senha",
                json={"email": user.email},
            )

            assert response.status_code == 200
            mock_send_email.assert_called_once()

            email_args = mock_send_email.call_args.kwargs
            assert email_args["to_email"] == user.email
            assert "token-de-teste-comprido-123456" in email_args["body"]
        finally:
            app.dependency_overrides.clear()


def test_confirm_reset_rejects_invalid_token():
    fake_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: fake_db

    with patch(
        "app.routers.password_reset.reset_user_password",
        return_value=False,
    ):
        try:
            response = client.post(
                "/usuarios/redefinir-senha",
                json={
                    "token": "token-invalido-comprido-123456",
                    "nova_senha": "NovaSenha123!",
                },
            )

            assert response.status_code == 400
            assert "Token inválido" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()


def test_confirm_reset_accepts_valid_token():
    fake_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: fake_db

    with patch(
        "app.routers.password_reset.reset_user_password",
        return_value=True,
    ):
        try:
            response = client.post(
                "/usuarios/redefinir-senha",
                json={
                    "token": "token-valido-comprido-123456",
                    "nova_senha": "NovaSenha123!",
                },
            )

            assert response.status_code == 200
            assert response.json()["message"] == "Senha redefinida com sucesso."
        finally:
            app.dependency_overrides.clear()


def test_confirm_reset_rejects_short_password():
    response = client.post(
        "/usuarios/redefinir-senha",
        json={
            "token": "token-valido-comprido-123456",
            "nova_senha": "curta",
        },
    )

    assert response.status_code == 422


def test_request_reset_invalidates_token_when_email_fails():
    from unittest.mock import MagicMock, patch

    fake_db = MagicMock()
    user = make_user()

    reset_token = MagicMock()
    reset_token.used_at = None

    # Primeira consulta: encontra o usuário.
    # Segunda consulta: encontra o token recém-criado.
    fake_db.query.return_value.filter.return_value.first.side_effect = [
        user,
        reset_token,
    ]

    app.dependency_overrides[get_db] = lambda: fake_db

    try:
        with patch(
            "app.routers.password_reset.create_password_reset_token",
            return_value="token-de-teste-comprido-123456",
        ), patch(
            "app.routers.password_reset.send_email",
            side_effect=Exception("Falha SMTP simulada"),
        ):
            response = client.post(
                "/usuarios/recuperar-senha",
                json={"email": user.email},
            )

        assert response.status_code == 503
        assert reset_token.used_at is not None
        fake_db.commit.assert_called_once()

    finally:
        app.dependency_overrides.clear()

