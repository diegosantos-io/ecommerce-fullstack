from datetime import datetime, UTC, timedelta
from unittest.mock import MagicMock, patch

from app.models import EmailOutbox, Order
from app.services.email_outbox_service import (
    BASE_RETRY_SECONDS,
    MAX_ATTEMPTS,
    PROCESSING_TIMEOUT_MINUTES,
    count_stale_processing_emails,
    process_next_email,
    recover_stale_processing_emails,
)


def criar_email(**overrides):
    email = MagicMock(spec=EmailOutbox)
    email.id = 10
    email.order_id = 2
    email.recipient = "cliente@example.com"
    email.subject = "Pagamento confirmado"
    email.body = "Seu pagamento foi confirmado."
    email.status = "pendente"
    email.attempts = 0
    email.next_attempt_at = datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=1)
    email.sent_at = None
    email.last_error = None

    for key, value in overrides.items():
        setattr(email, key, value)

    return email


def configurar_db(email=None, order=None):
    db = MagicMock()
    resultado = MagicMock()
    resultado.scalar_one_or_none.return_value = email
    db.execute.return_value = resultado
    db.get.side_effect = lambda model, object_id: (
        email if model is EmailOutbox and email and object_id == email.id
        else order if model is Order and order and object_id == email.order_id
        else None
    )
    return db


def test_processa_email_com_sucesso():
    email = criar_email()
    order = MagicMock(spec=Order)
    order.email_confirmacao_enviado = False
    db = configurar_db(email, order)

    with patch(
        "app.services.email_outbox_service.send_email"
    ) as mock_send:
        resultado = process_next_email(db)

    assert resultado is True
    mock_send.assert_called_once_with(
        to_email="cliente@example.com",
        subject="Pagamento confirmado",
        body="Seu pagamento foi confirmado.",
    )
    assert email.status == "enviado"
    assert email.attempts == 1
    assert email.sent_at is not None
    assert email.last_error is None
    assert order.email_confirmacao_enviado is True
    assert db.commit.call_count == 2


def test_retorna_false_quando_nao_existe_email_pendente():
    db = configurar_db(email=None)

    with patch(
        "app.services.email_outbox_service.send_email"
    ) as mock_send:
        resultado = process_next_email(db)

    assert resultado is False
    mock_send.assert_not_called()
    db.rollback.assert_called_once()
    db.commit.assert_not_called()


def test_reagenda_email_quando_envio_falha():
    email = criar_email()
    db = configurar_db(email)

    with patch(
        "app.services.email_outbox_service.send_email",
        side_effect=ConnectionError("SMTP indisponível"),
    ) as mock_send:
        antes = datetime.now(UTC).replace(tzinfo=None)
        resultado = process_next_email(db)
        depois = datetime.now(UTC).replace(tzinfo=None)

    assert resultado is True
    mock_send.assert_called_once()
    assert email.status == "pendente"
    assert email.attempts == 1
    assert email.last_error == "ConnectionError"

    atraso_minimo = antes + timedelta(seconds=BASE_RETRY_SECONDS)
    atraso_maximo = depois + timedelta(seconds=BASE_RETRY_SECONDS)
    assert atraso_minimo <= email.next_attempt_at <= atraso_maximo
    assert db.commit.call_count == 2


def test_marca_falha_apos_limite_de_tentativas():
    email = criar_email(attempts=MAX_ATTEMPTS - 1)
    db = configurar_db(email)

    with patch(
        "app.services.email_outbox_service.send_email",
        side_effect=ConnectionError("SMTP indisponível"),
    ):
        resultado = process_next_email(db)

    assert resultado is True
    assert email.attempts == MAX_ATTEMPTS
    assert email.status == "falha"
    assert email.last_error == "ConnectionError"
    assert db.commit.call_count == 2


def test_retorna_true_se_tarefa_for_excluida_apos_envio():
    email = criar_email()
    db = configurar_db(email)
    db.get.side_effect = lambda model, object_id: (
        None if model is EmailOutbox else None
    )

    with patch(
        "app.services.email_outbox_service.send_email"
    ) as mock_send:
        resultado = process_next_email(db)

    assert resultado is True
    mock_send.assert_called_once()
    db.rollback.assert_called_once()

def test_conta_emails_em_processamento_antigos():
    from datetime import datetime, UTC, timedelta
    from unittest.mock import MagicMock
    from app.services.email_outbox_service import count_stale_processing_emails

    db = MagicMock()
    db.execute.return_value.scalar_one.return_value = 2

    resultado = count_stale_processing_emails(db)

    assert resultado == 2
    db.execute.assert_called_once()


def test_retorna_zero_quando_nao_existem_emails_antigos():
    from unittest.mock import MagicMock
    from app.services.email_outbox_service import count_stale_processing_emails

    db = MagicMock()
    db.execute.return_value.scalar_one.return_value = 0

    resultado = count_stale_processing_emails(db)

    assert resultado == 0
    db.execute.assert_called_once()


def test_recupera_email_antigo_para_pendente():
    email = criar_email(
        status="processando",
        attempts=1,
        processing_started_at=(
            datetime.now(UTC).replace(tzinfo=None)
            - timedelta(minutes=PROCESSING_TIMEOUT_MINUTES + 1)
        ),
    )
    db = configurar_db(email)
    db.execute.return_value.scalars.return_value.all.return_value = [email]

    resultado = recover_stale_processing_emails(db)

    assert resultado == 1
    assert email.status == "pendente"
    assert email.processing_started_at is None
    assert email.last_error == (
        "Processamento interrompido; tarefa recuperada."
    )
    assert email.next_attempt_at > datetime.now(UTC).replace(tzinfo=None)
    db.commit.assert_called_once()


def test_recupera_email_antigo_sem_tentativas_restantes():
    email = criar_email(
        status="processando",
        attempts=MAX_ATTEMPTS,
        processing_started_at=(
            datetime.now(UTC).replace(tzinfo=None)
            - timedelta(minutes=PROCESSING_TIMEOUT_MINUTES + 1)
        ),
    )
    db = configurar_db(email)
    db.execute.return_value.scalars.return_value.all.return_value = [email]

    resultado = recover_stale_processing_emails(db)

    assert resultado == 1
    assert email.status == "falha"
    assert email.processing_started_at is None
    assert email.last_error == (
        "Processamento interrompido; tarefa recuperada."
    )
    db.commit.assert_called_once()

