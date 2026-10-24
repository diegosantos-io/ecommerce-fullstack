from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.database import get_db
from app.models import User
from app.schemas.order import OrderResponse
from app.services.cart_service import get_or_create_cart
from app.services.order_service import create_order_from_cart


router = APIRouter(
    prefix="/pedidos",
    tags=["Pedidos"],
)


@router.post(
    "/",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_order(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cart = get_or_create_cart(db, current_user.id)

    try:
        order = create_order_from_cart(db, cart)

        return {
            "id": order.id,
            "usuario_id": order.usuario_id,
            "status": order.status,
            "subtotal": order.subtotal,
            "frete": order.frete,
            "total": order.total,
            "itens": order.items,
            "criado_em": order.criado_em,
            "atualizado_em": order.atualizado_em,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )