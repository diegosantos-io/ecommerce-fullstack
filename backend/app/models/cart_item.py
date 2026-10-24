from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database.database import Base


class CartItem(Base):
    __tablename__ = "cart_items"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    carrinho_id: Mapped[int] = mapped_column(
        ForeignKey("carts.id"),
        nullable=False,
        index=True,
    )

    produto_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"),
        nullable=False,
        index=True,
    )

    quantidade: Mapped[int] = mapped_column(
        nullable=False,
        default=1,
    )
    