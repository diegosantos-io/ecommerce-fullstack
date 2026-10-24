from decimal import Decimal

import stripe

from app.database.database import settings


stripe.api_key = settings.STRIPE_SECRET_KEY


def decimal_to_cents(value: Decimal) -> int:
    return int(value * 100)


def create_checkout_session(
    order_id: int,
    total: Decimal,
) -> stripe.checkout.Session:
    total_in_cents = decimal_to_cents(total)

    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=[
            {
                "price_data": {
                    "currency": "brl",
                    "product_data": {
                        "name": f"Pedido #{order_id}",
                    },
                    "unit_amount": total_in_cents,
                },
                "quantity": 1,
            }
        ],
        success_url="http://localhost:5173/pagamento/sucesso",
        cancel_url="http://localhost:5173/pagamento/cancelado",
        metadata={
            "order_id": str(order_id),
        },
    )

    return session