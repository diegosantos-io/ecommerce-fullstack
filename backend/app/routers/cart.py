from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.database import get_db
from app.models import User
from app.schemas.cart import (
    CartItemCreate,
    CartItemResponse,
    CartItemUpdate,
    CartResponse,
)
from app.services.cart_service import (
    add_item_to_cart,
    get_cart_items,
    get_or_create_cart,
    get_cart_item,
    remove_cart_item,
    update_cart_item,
)


router = APIRouter(
    prefix="/carrinho",
    tags=["Carrinho"],
)


@router.get(
    "/",
    response_model=CartResponse,
)
def get_my_cart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cart = get_or_create_cart(
        db,
        current_user.id,
    )

    items = get_cart_items(
        db,
        cart.id,
    )

    return {
        "id": cart.id,
        "usuario_id": cart.usuario_id,
        "itens": items,
        "criado_em": cart.criado_em,
        "atualizado_em": cart.atualizado_em,
    }


@router.post(
    "/itens",
    response_model=CartItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_cart_item(
    item_data: CartItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cart = get_or_create_cart(
        db,
        current_user.id,
    )

    try:
        return add_item_to_cart(
            db,
            cart,
            item_data,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )


@router.put(
    "/itens/{item_id}",
    response_model=CartItemResponse,
)
def update_item(
    item_id: int,
    item_data: CartItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cart = get_or_create_cart(
        db,
        current_user.id,
    )

    cart_item = get_cart_item(
        db,
        cart.id,
        item_id,
    )

    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item não encontrado no carrinho.",
        )

    try:
        return update_cart_item(
            db,
            cart_item,
            item_data,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )


@router.delete(
    "/itens/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cart = get_or_create_cart(
        db,
        current_user.id,
    )

    cart_item = get_cart_item(
        db,
        cart.id,
        item_id,
    )

    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item não encontrado no carrinho.",
        )

    remove_cart_item(
        db,
        cart_item,
    )

    return None