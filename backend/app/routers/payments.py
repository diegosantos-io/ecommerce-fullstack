
import stripe

from datetime import datetime, UTC

from fastapi import APIRouter, Request, HTTPException, status, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.auth.dependencies import get_current_user
from app.database.database import SessionLocal, settings, get_db
from app.models import Order, User, StripeEvent, EmailOutbox
from app.models.email_outbox import utc_now_naive
from app.services.stripe_service import create_checkout_session


router = APIRouter(
    prefix="/pagamentos",
    tags=["Pagamentos"],
)


@router.post("/checkout/{order_id}")
def create_checkout(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = (
        db.query(Order)
        .filter(
            Order.id == order_id,
            Order.usuario_id == current_user.id,
        )
        .first()
    )

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido não encontrado.",
        )

    if order.status != "pendente":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este pedido não está disponível para pagamento.",
        )

    if order.total <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O valor do pedido deve ser maior que zero.",
        )

    try:
        session = create_checkout_session(
            order_id=order.id,
            total=order.total,
        )
    except Exception as error:
        print(f"Erro ao criar checkout: {type(error).__name__}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Não foi possível iniciar o pagamento. Tente novamente.",
        ) from error

    return {
        "message": "Checkout criado com sucesso.",
        "order_id": order.id,
        "checkout_url": session.url,
        "session_id": session.id,
    }


@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    signature = request.headers.get("stripe-signature")

    if not signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assinatura do Stripe ausente.",
        )

    try:
        event = stripe.Webhook.construct_event(
            payload,
            signature,
            settings.STRIPE_WEBHOOK_SECRET,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payload inválido.",
        ) from error
    except stripe.error.SignatureVerificationError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assinatura do webhook inválida.",
        ) from error

    if hasattr(event, "to_dict"):
        event = event.to_dict()

    event_type = event["type"]

    if event_type != "checkout.session.completed":
        return {"received": True}

    event_id = event.get("id")
    if not event_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID do evento Stripe ausente.",
        )

    session_data = event["data"]["object"]
    if hasattr(session_data, "to_dict"):
        session_data = session_data.to_dict()
    metadata = session_data.get("metadata") or {}
    order_id = metadata.get("order_id")

    if not order_id or session_data.get("payment_status") != "paid":
        return {"received": True}

    try:
        order_id = int(order_id)
    except (TypeError, ValueError):
        return {"received": True}

    db: Session = SessionLocal()

    try:
        stripe_event = (
            db.query(StripeEvent)
            .filter(StripeEvent.event_id == event_id)
            .with_for_update()
            .first()
        )

        if stripe_event and stripe_event.status == "processado":
            return {"received": True}

        if not stripe_event:
            stripe_event = StripeEvent(
                event_id=event_id,
                event_type=event_type,
                status="pendente",
            )
            db.add(stripe_event)

            try:
                # Detecta eventos duplicados antes de continuar.
                db.flush()
            except IntegrityError:
                db.rollback()

                existing_event = (
                    db.query(StripeEvent)
                    .filter(StripeEvent.event_id == event_id)
                    .first()
                )

                if existing_event:
                    return {"received": True}

                raise

        order = (
            db.query(Order)
            .filter(Order.id == order_id)
            .with_for_update()
            .first()
        )

        if not order:
            # Mantém o evento pendente para possibilitar nova entrega.
            db.commit()
            return {"received": True}

        # O bloqueio do pedido serializa eventos diferentes para o mesmo pedido.
        if order.status != "pago":
            order.status = "pago"

        if not order.email_confirmacao_enviado:
            existing_email = (
                db.query(EmailOutbox)
                .filter(EmailOutbox.order_id == order.id)
                .with_for_update()
                .first()
            )

            if not existing_email:
                db.add(
                    EmailOutbox(
                        order_id=order.id,
                        recipient=order.usuario.email,
                        subject=f"Pagamento confirmado - Pedido #{order.id}",
                        body=f"""Olá!

Seu pagamento foi confirmado com sucesso.

Pedido: #{order.id}
Valor total: R$ {order.total:.2f}
Status: Pago

Obrigado por comprar conosco!

E-commerce Full Stack
""",
                        status="pendente",
                        attempts=0,
                        next_attempt_at=utc_now_naive(),
                    )
                )

        stripe_event.status = "processado"
        stripe_event.processado_em = datetime.now(UTC).replace(tzinfo=None)

        # Pagamento, tarefa de e-mail e estado do evento são persistidos juntos.
        db.commit()

        return {"received": True}

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
