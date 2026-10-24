from datetime import datetime, UTC, timedelta
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models import EmailOutbox, Order
from app.services.email_service import send_email


MAX_ATTEMPTS = 5
BASE_RETRY_SECONDS = 60
PROCESSING_TIMEOUT_MINUTES = 10


def count_stale_processing_emails(db: Session) -> int:
    """
    Conta tarefas que ficaram em processamento por mais de 10 minutos.
    Não altera o status nem tenta reenviar e-mails.
    """
    cutoff = (
        datetime.now(UTC).replace(tzinfo=None)
        - timedelta(minutes=PROCESSING_TIMEOUT_MINUTES)
    )

    result = db.execute(
        select(func.count())
        .select_from(EmailOutbox)
        .where(
            EmailOutbox.status == "processando",
            EmailOutbox.processing_started_at.is_not(None),
            EmailOutbox.processing_started_at <= cutoff,
        )
    )

    return result.scalar_one()


def recover_stale_processing_emails(db: Session) -> int:
    """
    Recupera tarefas que ficaram em processamento por mais de 10 minutos.
    Retorna a quantidade de tarefas recuperadas.
    """
    now = datetime.now(UTC).replace(tzinfo=None)
    cutoff = now - timedelta(minutes=PROCESSING_TIMEOUT_MINUTES)

    try:
        emails = db.execute(
            select(EmailOutbox)
            .where(
                EmailOutbox.status == "processando",
                EmailOutbox.processing_started_at.is_not(None),
                EmailOutbox.processing_started_at <= cutoff,
            )
            .order_by(EmailOutbox.id)
            .with_for_update(skip_locked=True)
        ).scalars().all()

        recovered = 0

        for email in emails:
            email.processing_started_at = None
            email.last_error = "Processamento interrompido; tarefa recuperada."

            if email.attempts >= MAX_ATTEMPTS:
                email.status = "falha"
            else:
                email.status = "pendente"
                delay = BASE_RETRY_SECONDS * (2 ** (email.attempts - 1))
                email.next_attempt_at = now + timedelta(seconds=delay)

            recovered += 1

        db.commit()
        return recovered

    except Exception:
        db.rollback()
        raise



def process_next_email(db: Session) -> bool:
    """
    Processa um e-mail pendente.
    Retorna True se encontrou uma tarefa; False caso não exista nenhuma.
    """
    now = datetime.now(UTC).replace(tzinfo=None)

    try:
        email = db.execute(
            select(EmailOutbox)
            .where(
                EmailOutbox.status == "pendente",
                EmailOutbox.next_attempt_at <= now,
            )
            .order_by(EmailOutbox.id)
            .with_for_update(skip_locked=True)
            .limit(1)
        ).scalar_one_or_none()

        if email is None:
            db.rollback()
            return False

        # Marca como em processamento e libera o bloqueio antes do SMTP.
        # Isso evita manter uma transação de banco aberta durante a rede.
        email.status = "processando"
        email.processing_started_at = now
        email.attempts += 1
        email_id = email.id
        recipient = email.recipient
        subject = email.subject
        body = email.body
        order_id = email.order_id
        db.commit()

    except Exception:
        db.rollback()
        raise

    try:
        send_email(
            to_email=recipient,
            subject=subject,
            body=body,
        )
    except Exception as error:
        db.rollback()

        email = db.get(EmailOutbox, email_id)
        if email is None:
            return True

        email.last_error = type(error).__name__
        email.processing_started_at = None

        if email.attempts >= MAX_ATTEMPTS:
            email.status = "falha"
        else:
            email.status = "pendente"
            delay = BASE_RETRY_SECONDS * (2 ** (email.attempts - 1))
            email.next_attempt_at = datetime.now(UTC).replace(tzinfo=None) + timedelta(
                seconds=delay
            )

        db.commit()
        return True

    email = db.get(EmailOutbox, email_id)
    if email is None:
        db.rollback()
        return True

    email.status = "enviado"
    email.sent_at = datetime.now(UTC).replace(tzinfo=None)
    email.processing_started_at = None
    email.last_error = None

    order = db.get(Order, order_id)
    if order is not None:
        order.email_confirmacao_enviado = True

    db.commit()
    return True
