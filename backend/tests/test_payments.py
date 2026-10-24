from decimal import Decimal
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.auth.dependencies import get_current_user
from app.database.database import get_db
from app.models import EmailOutbox


client = TestClient(app)



def configurar_mock_webhook(fake_db, fake_order, fake_stripe_event=None):
    """Configura consultas simuladas para o webhook do Stripe."""
    from app.models import EmailOutbox, Order, StripeEvent

    fake_stripe_event = fake_stripe_event or MagicMock()
    fake_stripe_event.status = "pendente"

    def query_side_effect(model):
        query = MagicMock()

        if model is StripeEvent:
            query.filter.return_value.with_for_update.return_value.first.return_value = (
                fake_stripe_event
            )
        elif model is Order:
            query.filter.return_value.with_for_update.return_value.first.return_value = (
                fake_order
            )
        elif model is EmailOutbox:
            query.filter.return_value.with_for_update.return_value.first.return_value = (
                None
            )
        else:
            query.filter.return_value.with_for_update.return_value.first.return_value = None

        return query

    fake_db.query.side_effect = query_side_effect
    return fake_stripe_event



fake_user = MagicMock()
fake_user.id = 1
fake_user.ativo = True
fake_user.role = "user"


def override_current_user():
    return fake_user

# ============================================================
# CHECKOUT
# ============================================================

def test_checkout_order_not_found():
    fake_db = MagicMock()
    fake_db.query.return_value.filter.return_value.first.return_value = None

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_db] = lambda: fake_db

    try:
        with patch(
            "app.routers.payments.create_checkout_session"
        ) as mock_checkout:
            response = client.post("/pagamentos/checkout/999999")

        assert response.status_code == 404
        assert response.json()["detail"] == "Pedido não encontrado."
        mock_checkout.assert_not_called()
    finally:
        app.dependency_overrides.clear()


def test_checkout_order_not_available_for_payment():
    fake_order = MagicMock()
    fake_order.id = 2
    fake_order.usuario_id = 1
    fake_order.status = "pago"

    fake_db = MagicMock()
    fake_db.query.return_value.filter.return_value.first.return_value = fake_order

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_db] = lambda: fake_db

    try:
        with patch(
            "app.routers.payments.create_checkout_session"
        ) as mock_checkout:
            response = client.post("/pagamentos/checkout/2")

        assert response.status_code == 400
        assert response.json()["detail"] == (
            "Este pedido não está disponível para pagamento."
        )
        mock_checkout.assert_not_called()
    finally:
        app.dependency_overrides.clear()


def test_checkout_creates_session_for_pending_order():
    fake_order = MagicMock()
    fake_order.id = 2
    fake_order.usuario_id = 1
    fake_order.status = "pendente"
    fake_order.total = Decimal("399.80")

    fake_db = MagicMock()
    fake_db.query.return_value.filter.return_value.first.return_value = fake_order

    fake_session = MagicMock()
    fake_session.url = "https://checkout.stripe.com/test"
    fake_session.id = "cs_test_fake"

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_db] = lambda: fake_db

    try:
        with patch(
            "app.routers.payments.create_checkout_session",
            return_value=fake_session,
        ) as mock_checkout:
            response = client.post("/pagamentos/checkout/2")

        assert response.status_code == 200
        assert response.json() == {
            "message": "Checkout criado com sucesso.",
            "order_id": 2,
            "checkout_url": "https://checkout.stripe.com/test",
            "session_id": "cs_test_fake",
        }

        mock_checkout.assert_called_once_with(
            order_id=2,
            total=Decimal("399.80"),
        )
    finally:
        app.dependency_overrides.clear()


# ============================================================
# WEBHOOK - CHECKOUT SESSION COMPLETED
# ============================================================

def test_webhook_checkout_session_completed_marks_order_as_paid():
    fake_session = MagicMock()

    fake_session.to_dict.return_value = {
        "id": "cs_test_fake",
        "metadata": {
            "order_id": "2",
        },
        "payment_status": "paid",
    }

    fake_event = {
        "id": "evt_test_fake",
        "type": "checkout.session.completed",
        "data": {
            "object": fake_session,
        },
    }

    fake_order = MagicMock()
    fake_order.id = 2
    fake_order.status = "pendente"
    fake_order.total = Decimal("399.80")
    fake_order.usuario.email = "diegoo.ecommerce@gmail.com"

    fake_stripe_event = MagicMock()
    fake_stripe_event.status = "pendente"

    fake_db = MagicMock()
    fake_db.query.return_value.filter.return_value.with_for_update.return_value.first.side_effect = [
        None,
        fake_order,
        fake_stripe_event,
    ]

    with patch(
        "app.routers.payments.stripe.Webhook.construct_event",
        return_value=fake_event,
    ), patch(
        "app.routers.payments.SessionLocal",
        return_value=fake_db,
    ):
        response = client.post(
            "/pagamentos/webhook",
            content=b'{"fake":"payload"}',
            headers={"stripe-signature": "fake_signature"},
        )

    assert response.status_code == 200
    assert response.json() == {"received": True}
    assert fake_order.status == "pago"
    assert fake_db.commit.call_count == 1


def test_webhook_does_not_mark_order_paid_when_payment_is_not_paid():
    fake_session = MagicMock()

    fake_session.to_dict.return_value = {
        "id": "cs_test_fake",
        "metadata": {
            "order_id": "2",
        },
        "payment_status": "unpaid",
    }

    fake_event = {
        "id": "evt_test_fake",
        "type": "checkout.session.completed",
        "data": {
            "object": fake_session,
        },
    }

    fake_order = MagicMock()
    fake_order.id = 2
    fake_order.status = "pendente"

    fake_db = MagicMock()

    with patch(
        "app.routers.payments.stripe.Webhook.construct_event",
        return_value=fake_event,
    ), patch(
        "app.routers.payments.SessionLocal",
        return_value=fake_db,
    ):
        response = client.post(
            "/pagamentos/webhook",
            content=b'{"fake":"payload"}',
            headers={"stripe-signature": "fake_signature"},
        )

    assert response.status_code == 200
    assert response.json() == {"received": True}
    assert fake_order.status == "pendente"
    fake_db.commit.assert_not_called()


def test_webhook_does_not_update_already_paid_order():
    fake_session = MagicMock()

    fake_session.to_dict.return_value = {
        "id": "cs_test_fake",
        "metadata": {
            "order_id": "2",
        },
        "payment_status": "paid",
    }

    fake_event = {
        "id": "evt_test_fake",
        "type": "checkout.session.completed",
        "data": {
            "object": fake_session,
        },
    }

    fake_order = MagicMock()
    fake_order.id = 2
    fake_order.status = "pago"

    fake_db = MagicMock()
    configurar_mock_webhook(fake_db, fake_order)

    with patch(
        "app.routers.payments.stripe.Webhook.construct_event",
        return_value=fake_event,
    ), patch(
        "app.routers.payments.SessionLocal",
        return_value=fake_db,
    ):
        response = client.post(
            "/pagamentos/webhook",
            content=b'{"fake":"payload"}',
            headers={"stripe-signature": "fake_signature"},
        )

    assert response.status_code == 200
    assert response.json() == {"received": True}
    assert fake_order.status == "pago"
    fake_db.commit.assert_called_once()


def test_webhook_order_not_found():
    fake_session = MagicMock()

    fake_session.to_dict.return_value = {
        "id": "cs_test_fake",
        "metadata": {
            "order_id": "999999",
        },
        "payment_status": "paid",
    }

    fake_event = {
        "id": "evt_test_fake",
        "type": "checkout.session.completed",
        "data": {
            "object": fake_session,
        },
    }

    fake_db = MagicMock()
    configurar_mock_webhook(fake_db, None)

    with patch(
        "app.routers.payments.stripe.Webhook.construct_event",
        return_value=fake_event,
    ), patch(
        "app.routers.payments.SessionLocal",
        return_value=fake_db,
    ):
        response = client.post(
            "/pagamentos/webhook",
            content=b'{"fake":"payload"}',
            headers={"stripe-signature": "fake_signature"},
        )

    assert response.status_code == 200
    assert response.json() == {"received": True}
    fake_db.commit.assert_called_once()


# ============================================================
# WEBHOOK - VALIDAÇÃO
# ============================================================

def test_webhook_requires_stripe_signature():
    response = client.post(
        "/pagamentos/webhook",
        content=b'{"fake":"payload"}',
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Assinatura do Stripe ausente."


def test_webhook_rejects_invalid_payload():
    with patch(
        "app.routers.payments.stripe.Webhook.construct_event",
        side_effect=ValueError(),
    ):
        response = client.post(
            "/pagamentos/webhook",
            content=b'payload-invalido',
            headers={"stripe-signature": "fake_signature"},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Payload inválido."


def test_webhook_rejects_invalid_signature():
    import stripe

    with patch(
        "app.routers.payments.stripe.Webhook.construct_event",
        side_effect=stripe.error.SignatureVerificationError(
            "Assinatura inválida.",
            "fake_signature",
        ),
    ):
        response = client.post(
            "/pagamentos/webhook",
            content=b'{"fake":"payload"}',
            headers={"stripe-signature": "fake_signature"},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Assinatura do webhook inválida."


def test_webhook_ignores_unrelated_event():
    fake_event = {
        "type": "payment_intent.succeeded",
        "data": {
            "object": {},
        },
    }

    with patch(
        "app.routers.payments.stripe.Webhook.construct_event",
        return_value=fake_event,
    ):
        response = client.post(
            "/pagamentos/webhook",
            content=b'{"fake":"payload"}',
            headers={"stripe-signature": "fake_signature"},
        )

    assert response.status_code == 200
    assert response.json() == {"received": True}


# ============================================================
# WEBHOOK - E-MAIL
# ============================================================


def test_webhook_sends_payment_confirmation_email():
    fake_session = MagicMock()
    fake_session.to_dict.return_value = {
        "id": "cs_test_fake",
        "metadata": {"order_id": "2"},
        "payment_status": "paid",
    }

    fake_event = {
        "id": "evt_test_fake",
        "type": "checkout.session.completed",
        "data": {"object": fake_session},
    }

    fake_order = MagicMock()
    fake_order.id = 2
    fake_order.status = "pendente"
    fake_order.total = Decimal("399.80")
    fake_order.email_confirmacao_enviado = False
    fake_order.usuario.email = "diegoo.ecommerce@gmail.com"

    fake_db = MagicMock()
    configurar_mock_webhook(fake_db, fake_order)

    with patch(
        "app.routers.payments.stripe.Webhook.construct_event",
        return_value=fake_event,
    ), patch(
        "app.routers.payments.SessionLocal",
        return_value=fake_db,
    ):
        response = client.post(
            "/pagamentos/webhook",
            content=b'{"fake":"payload"}',
            headers={"stripe-signature": "fake_signature"},
        )

    assert response.status_code == 200
    assert fake_order.status == "pago"

    email_tasks = [
        call.args[0]
        for call in fake_db.add.call_args_list
        if call.args and isinstance(call.args[0], EmailOutbox)
    ]

    assert len(email_tasks) == 1

    email = email_tasks[0]
    assert email.order_id == 2
    assert email.recipient == "diegoo.ecommerce@gmail.com"
    assert email.subject == "Pagamento confirmado - Pedido #2"
    assert "Olá!" in email.body
    assert "Seu pagamento foi confirmado com sucesso." in email.body
    assert "Pedido: #2" in email.body
    assert "Valor total: R$ 399.80" in email.body
    assert "Status: Pago" in email.body
    assert "Obrigado por comprar conosco!" in email.body
    assert email.status == "pendente"
    assert email.attempts == 0


def test_webhook_does_not_duplicate_email_for_already_paid_order():
    fake_session = MagicMock()
    fake_session.to_dict.return_value = {
        "id": "cs_test_fake",
        "metadata": {"order_id": "2"},
        "payment_status": "paid",
    }

    fake_event = {
        "id": "evt_test_fake",
        "type": "checkout.session.completed",
        "data": {"object": fake_session},
    }

    fake_order = MagicMock()
    fake_order.id = 2
    fake_order.status = "pago"
    fake_order.email_confirmacao_enviado = True

    fake_db = MagicMock()
    configurar_mock_webhook(fake_db, fake_order)

    with patch(
        "app.routers.payments.stripe.Webhook.construct_event",
        return_value=fake_event,
    ), patch(
        "app.routers.payments.SessionLocal",
        return_value=fake_db,
    ):
        response = client.post(
            "/pagamentos/webhook",
            content=b'{"fake":"payload"}',
            headers={"stripe-signature": "fake_signature"},
        )

    assert response.status_code == 200
    assert fake_order.status == "pago"

    email_tasks = [
        call.args[0]
        for call in fake_db.add.call_args_list
        if call.args and isinstance(call.args[0], EmailOutbox)
    ]
    assert email_tasks == []


def test_webhook_queues_email_without_sending_it():
    fake_session = MagicMock()
    fake_session.to_dict.return_value = {
        "id": "cs_test_fake",
        "metadata": {"order_id": "2"},
        "payment_status": "paid",
    }

    fake_event = {
        "id": "evt_test_fake",
        "type": "checkout.session.completed",
        "data": {"object": fake_session},
    }

    fake_order = MagicMock()
    fake_order.id = 2
    fake_order.status = "pendente"
    fake_order.total = Decimal("399.80")
    fake_order.email_confirmacao_enviado = False
    fake_order.usuario.email = "teste@example.com"

    fake_db = MagicMock()
    configurar_mock_webhook(fake_db, fake_order)

    with patch(
        "app.routers.payments.stripe.Webhook.construct_event",
        return_value=fake_event,
    ), patch(
        "app.routers.payments.SessionLocal",
        return_value=fake_db,
    ), patch(
        "app.services.email_outbox_service.send_email"
    ) as mock_send_email:
        response = client.post(
            "/pagamentos/webhook",
            content=b'{"fake":"payload"}',
            headers={"stripe-signature": "fake_signature"},
        )

    assert response.status_code == 200
    assert response.json() == {"received": True}
    assert fake_order.status == "pago"
    mock_send_email.assert_not_called()

    email_tasks = [
        call.args[0]
        for call in fake_db.add.call_args_list
        if call.args and isinstance(call.args[0], EmailOutbox)
    ]
    assert len(email_tasks) == 1
    assert email_tasks[0].recipient == "teste@example.com"


def test_webhook_does_not_duplicate_existing_email_task():
    fake_session = MagicMock()
    fake_session.to_dict.return_value = {
        "id": "cs_test_fake",
        "metadata": {"order_id": "2"},
        "payment_status": "paid",
    }

    fake_event = {
        "id": "evt_test_fake",
        "type": "checkout.session.completed",
        "data": {"object": fake_session},
    }

    fake_order = MagicMock()
    fake_order.id = 2
    fake_order.status = "pago"
    fake_order.total = Decimal("399.80")
    fake_order.email_confirmacao_enviado = False
    fake_order.usuario.email = "teste@example.com"

    fake_db = MagicMock()
    configurar_mock_webhook(fake_db, fake_order)

    # Simula uma tarefa existente apenas na consulta de EmailOutbox.
    consulta_original = fake_db.query.side_effect

    def query_com_email_existente(model):
        query = MagicMock()

        if model is EmailOutbox:
            query.filter.return_value.with_for_update.return_value.first.return_value = (
                MagicMock(spec=EmailOutbox)
            )
        else:
            return consulta_original(model)

        return query

    fake_db.query.side_effect = query_com_email_existente

    with patch(
        "app.routers.payments.stripe.Webhook.construct_event",
        return_value=fake_event,
    ), patch(
        "app.routers.payments.SessionLocal",
        return_value=fake_db,
    ):
        response = client.post(
            "/pagamentos/webhook",
            content=b'{"fake":"payload"}',
            headers={"stripe-signature": "fake_signature"},
        )

    assert response.status_code == 200
    assert response.json() == {"received": True}

    email_tasks = [
        call.args[0]
        for call in fake_db.add.call_args_list
        if call.args and isinstance(call.args[0], EmailOutbox)
    ]
    assert email_tasks == []


def test_webhook_ignores_already_processed_stripe_event():
    fake_session = MagicMock()
    fake_session.to_dict.return_value = {
        "id": "cs_test_fake",
        "metadata": {"order_id": "2"},
        "payment_status": "paid",
    }

    fake_event = {
        "id": "evt_test_already_processed",
        "type": "checkout.session.completed",
        "data": {"object": fake_session},
    }

    processed_event = MagicMock()
    processed_event.status = "processado"

    fake_db = MagicMock()
    fake_db.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = (
        processed_event
    )

    with patch(
        "app.routers.payments.stripe.Webhook.construct_event",
        return_value=fake_event,
    ), patch(
        "app.routers.payments.SessionLocal",
        return_value=fake_db,
    ):
        response = client.post(
            "/pagamentos/webhook",
            content=b'{"fake":"payload"}',
            headers={"stripe-signature": "fake_signature"},
        )

    assert response.status_code == 200
    assert response.json() == {"received": True}
    fake_db.add.assert_not_called()
    fake_db.commit.assert_not_called()
