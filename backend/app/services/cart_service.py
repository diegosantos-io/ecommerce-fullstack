from sqlalchemy.orm import Session

from app.models import Cart, CartItem, Product
from app.schemas.cart import (
    CartItemCreate,
    CartItemUpdate,
)


def get_cart_by_user_id(
    db: Session,
    user_id: int,
) -> Cart | None:
    return (
        db.query(Cart)
        .filter(Cart.usuario_id == user_id)
        .first()
    )


def create_cart(
    db: Session,
    user_id: int,
) -> Cart:
    cart = Cart(
        usuario_id=user_id,
    )

    db.add(cart)
    db.commit()
    db.refresh(cart)

    return cart


def get_or_create_cart(
    db: Session,
    user_id: int,
) -> Cart:
    cart = get_cart_by_user_id(
        db,
        user_id,
    )

    if cart:
        return cart

    return create_cart(
        db,
        user_id,
    )


def get_cart_items(
    db: Session,
    cart_id: int,
) -> list[CartItem]:
    return (
        db.query(CartItem)
        .filter(CartItem.carrinho_id == cart_id)
        .order_by(CartItem.id)
        .all()
    )


def get_cart_item(
    db: Session,
    cart_id: int,
    item_id: int,
) -> CartItem | None:
    return (
        db.query(CartItem)
        .filter(
            CartItem.id == item_id,
            CartItem.carrinho_id == cart_id,
        )
        .first()
    )


def add_item_to_cart(
    db: Session,
    cart: Cart,
    item_data: CartItemCreate,
) -> CartItem:
    product = (
        db.query(Product)
        .filter(
            Product.id == item_data.produto_id,
            Product.ativo.is_(True),
        )
        .first()
    )

    if not product:
        raise ValueError("Produto não encontrado ou inativo.")

    if product.estoque < item_data.quantidade:
        raise ValueError("Estoque insuficiente.")

    existing_item = (
        db.query(CartItem)
        .filter(
            CartItem.carrinho_id == cart.id,
            CartItem.produto_id == item_data.produto_id,
        )
        .first()
    )

    if existing_item:
        nova_quantidade = (
            existing_item.quantidade
            + item_data.quantidade
        )

        if product.estoque < nova_quantidade:
            raise ValueError("Estoque insuficiente.")

        existing_item.quantidade = nova_quantidade

        db.commit()
        db.refresh(existing_item)

        return existing_item

    cart_item = CartItem(
        carrinho_id=cart.id,
        produto_id=item_data.produto_id,
        quantidade=item_data.quantidade,
    )

    db.add(cart_item)
    db.commit()
    db.refresh(cart_item)

    return cart_item


def update_cart_item(
    db: Session,
    cart_item: CartItem,
    item_data: CartItemUpdate,
) -> CartItem:
    product = (
        db.query(Product)
        .filter(
            Product.id == cart_item.produto_id,
            Product.ativo.is_(True),
        )
        .first()
    )

    if not product:
        raise ValueError("Produto não encontrado ou inativo.")

    if product.estoque < item_data.quantidade:
        raise ValueError("Estoque insuficiente.")

    cart_item.quantidade = item_data.quantidade

    db.commit()
    db.refresh(cart_item)

    return cart_item


def remove_cart_item(
    db: Session,
    cart_item: CartItem,
) -> None:
    db.delete(cart_item)
    db.commit()