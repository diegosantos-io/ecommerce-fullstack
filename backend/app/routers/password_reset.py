import hashlib
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from datetime import datetime, timezone
from app.models.password_reset_token import PasswordResetToken
from app.database.database import get_db
from app.models import User
from app.schemas.password_reset import (
    PasswordResetRequest,
    PasswordResetConfirm,
    PasswordResetMessage,
)
from app.services.email_service import send_email
from app.services.password_reset_service import (
    create_password_reset_token,
    reset_user_password,
)


router = APIRouter(
    prefix="/usuarios",
    tags=["Recuperação de senha"],
)


@router.post(
    "/recuperar-senha",
    response_model=PasswordResetMessage,
)
def request_password_reset(
    request_data: PasswordResetRequest,
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(User.email == str(request_data.email))
        .first()
    )

    # A resposta é a mesma, exista ou não a conta.
    message = (
        "Se o e-mail estiver cadastrado, "
        "você receberá as instruções para recuperar a senha."
    )

    if not user or not user.ativo:
        return {"message": message}

    raw_token = create_password_reset_token(db, user)

    reset_url = (
        "http://localhost:5173/redefinir-senha?token="
        + quote(raw_token, safe="")
    )

    try:
        send_email(
            to_email=user.email,
            subject="Recuperação de senha - E-commerce",
            body=(
                f"Olá, {user.nome}!\n\n"
                "Recebemos uma solicitação para redefinir sua senha.\n\n"
                f"Acesse este link para continuar:\n{reset_url}\n\n"
                "O link expira em 30 minutos e só pode ser utilizado uma vez.\n"
                "Se você não solicitou a recuperação, ignore este e-mail."
            ),
        )
    except Exception:
        # Invalida somente o token criado para esta solicitação.
        token_hash = hashlib.sha256(
            raw_token.encode("utf-8")
        ).hexdigest()

        try:
            reset_token = (
                db.query(PasswordResetToken)
                .filter(
                    PasswordResetToken.token_hash == token_hash
                )
                .first()
            )

            if reset_token and reset_token.used_at is None:
                reset_token.used_at = datetime.now(timezone.utc)
                db.commit()

        except Exception:
            db.rollback()

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Não foi possível enviar o e-mail de recuperação. "
                "Tente novamente."
            ),
        )

    return {"message": message}


@router.post(
    "/redefinir-senha",
    response_model=PasswordResetMessage,
)
def confirm_password_reset(
    request_data: PasswordResetConfirm,
    db: Session = Depends(get_db),
):
    success = reset_user_password(
        db=db,
        raw_token=request_data.token,
        new_password=request_data.nova_senha,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido, expirado ou já utilizado.",
        )

    return {
        "message": "Senha redefinida com sucesso."
    }
