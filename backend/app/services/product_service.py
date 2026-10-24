from sqlalchemy.orm import Session

from app.models import Product
from app.schemas.product import ProductCreate, ProductUpdate


def get_product_by_id(
    db: Session,
    product_id: int,
) -> Product | None:
    return (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )


def get_products(
    db: Session,
) -> list[Product]:
    return (
        db.query(Product)
        .order_by(Product.nome)
        .all()
    )


def create_product(
    db: Session,
    product_data: ProductCreate,
) -> Product:
    product = Product(
        nome=product_data.nome,
        descricao=product_data.descricao,
        preco=product_data.preco,
        estoque=product_data.estoque,
        imagem_url=product_data.imagem_url,
        categoria_id=product_data.categoria_id,
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    return product


def update_product(
    db: Session,
    product: Product,
    product_data: ProductUpdate,
) -> Product:
    update_data = product_data.model_dump(
        exclude_unset=True,
    )

    for field, value in update_data.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)

    return product


def delete_product(
    db: Session,
    product: Product,
) -> None:
    db.delete(product)
    db.commit()