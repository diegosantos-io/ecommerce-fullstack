import json
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func

from app.database.database import SessionLocal, engine
from app.main import app
from app.models import EmailOutbox, Order, StripeEvent


TEST_ORDER_ID = 1


def test_webhook_concorrente_cria_apenas_um_email(monkeypatch):
    # Impede que este teste altere o banco principal.
    if engine.url.database != "ecommerce_test" or engine.url.port != 5434:
        pytest.fail(
            "Teste bloqueado: configure DATABASE_URL para "
            "ecommerce_test na porta 5434."
        )

    event_prefix = f"evt_concurrency_{uuid4().hex}"
    event_ids = [f"{event_prefix}_1", f"{event_prefix}_2"]

    # Prepara exclusivamente o pedido fictício do banco de testes.
    with SessionLocal() as db:
        order = db.query(Order).filter(Order.id == TEST_ORDER_ID).first()
        if order is None:
            pytest.fail("Pedido fictício #1 não encontrado no banco de testes.")

        db.query(EmailOutbox).filter(
            EmailOutbox.order_id == TEST_ORDER_ID
        ).delete(synchronize_session=False)

        db.query(StripeEvent).filter(
            StripeEvent.event_id.in_(event_ids)
        ).delete(synchronize_session=False)

        order.status = "pendente"
        order.email_confirmacao_enviado = False
        db.commit()

    # Converte o payload fictício em evento; não acessa a API do Stripe.
    def fake_construct_event(payload, signature, secret):
        return json.loads(payload)

    monkeypatch.setattr(
        "app.routers.payments.stripe.Webhook.construct_event",
        fake_construct_event,
    )

    payloads = [
        json.dumps(
            {
                "id": event_id,
                "type": "checkout.session.completed",
                "data": {
                    "object": {
                        "id": f"cs_test_{index}",
                        "metadata": {"order_id": str(TEST_ORDER_ID)},
                        "payment_status": "paid",
                    }
                },
            }
        ).encode()
        for index, event_id in enumerate(event_ids, start=1)
    ]

    def send_webhook(payload):
        with TestClient(app) as client:
            return client.post(
                "/pagamentos/webhook",
                content=payload,
                headers={"stripe-signature": "fake-signature"},
            )

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(send_webhook, payload)
                for payload in payloads
            ]
            responses = [future.result(timeout=20) for future in futures]

        assert all(response.status_code == 200 for response in responses), [
            (response.status_code, response.text) for response in responses
        ]

        with SessionLocal() as db:
            order = db.query(Order).filter(
                Order.id == TEST_ORDER_ID
            ).one()

            email_count = (
                db.query(func.count(EmailOutbox.id))
                .filter(EmailOutbox.order_id == TEST_ORDER_ID)
                .scalar()
            )

            event_count = (
                db.query(func.count(StripeEvent.id))
                .filter(StripeEvent.event_id.in_(event_ids))
                .scalar()
            )

            assert order.status == "pago"
            assert email_count == 1, (
                f"Esperava 1 tarefa de e-mail, encontrei {email_count}."
            )
            assert event_count == 2, (
                f"Esperava 2 eventos registrados, encontrei {event_count}."
            )

    finally:
        # Remove apenas os dados criados para este teste.
        with SessionLocal() as db:
            db.query(EmailOutbox).filter(
                EmailOutbox.order_id == TEST_ORDER_ID
            ).delete(synchronize_session=False)

            db.query(StripeEvent).filter(
                StripeEvent.event_id.in_(event_ids)
            ).delete(synchronize_session=False)

            order = db.query(Order).filter(
                Order.id == TEST_ORDER_ID
            ).first()

            if order is not None:
                order.status = "pendente"
                order.email_confirmacao_enviado = False

            db.commit()
