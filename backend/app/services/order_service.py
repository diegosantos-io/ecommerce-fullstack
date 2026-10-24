from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import Cart, CartItem, Order, OrderItem, Product


def calculate_cart_subtotal(db: Session, cart_id: int) -> Decimal:
    items = (
        db.query(CartItem)
        .filter(CartItem.carrinho_id == cart_id)
        .all()
    )

    subtotal = Decimal("0.00")

    for item in items:
        product = (
            db.query(Product)
            .filter(Product.id == item.produto_id)
            .first()
        )

        if not product:
            raise ValueError("Produto do carrinho não encontrado.")

        subtotal += product.preco * item.quantidade

    return subtotal


def create_order_from_cart(
    db: Session,
    cart: Cart,
) -> Order:
    cart_items = (
        db.query(CartItem)
        .filter(CartItem.carrinho_id == cart.id)
        .all()
    )

    if not cart_items:
        raise ValueError("O carrinho está vazio.")

    subtotal = Decimal("0.00")
    order_items_data = []

    for cart_item in cart_items:
        product = (
            db.query(Product)
            .filter(
                Product.id == cart_item.produto_id,
                Product.ativo.is_(True),
            )
            .first()
        )

        if not product:
            raise ValueError(
                "Um dos produtos do carrinho não está disponível."
            )

        if product.estoque < cart_item.quantidade:
            raise ValueError(
                f"Estoque insuficiente para o produto '{product.nome}'."
            )

        item_subtotal = product.preco * cart_item.quantidade

        subtotal += item_subtotal

        order_items_data.append(
            {
                "produto_id": product.id,
                "quantidade": cart_item.quantidade,
                "preco_unitario": product.preco,
                "subtotal": item_subtotal,
                "product": product,
            }
        )

    frete = Decimal("0.00")
    total = subtotal + frete

    order = Order(
        usuario_id=cart.usuario_id,
        status="pendente",
        subtotal=subtotal,
        frete=frete,
        total=total,
    )

    db.add(order)
    db.flush()

    for item_data in order_items_data:
        product = item_data["product"]

        product.estoque -= item_data["quantidade"]

        order_item = OrderItem(
            pedido_id=order.id,
            produto_id=item_data["produto_id"],
            quantidade=item_data["quantidade"],
            preco_unitario=item_data["preco_unitario"],
            subtotal=item_data["subtotal"],
        )

        db.add(order_item)

    for cart_item in cart_items:
        db.delete(cart_item)

    db.commit()
    db.refresh(order)

    return order