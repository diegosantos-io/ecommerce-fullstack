from sqlalchemy.orm import Session

from app.models import Category
from app.schemas.category import CategoryCreate, CategoryUpdate


def get_category_by_id(
    db: Session,
    category_id: int,
) -> Category | None:
    return (
        db.query(Category)
        .filter(Category.id == category_id)
        .first()
    )


def get_category_by_name(
    db: Session,
    nome: str,
) -> Category | None:
    return (
        db.query(Category)
        .filter(Category.nome == nome)
        .first()
    )


def get_categories(
    db: Session,
) -> list[Category]:
    return (
        db.query(Category)
        .order_by(Category.nome)
        .all()
    )


def create_category(
    db: Session,
    category_data: CategoryCreate,
) -> Category:
    category = Category(
        nome=category_data.nome,
        descricao=category_data.descricao,
    )

    db.add(category)
    db.commit()
    db.refresh(category)

    return category


def update_category(
    db: Session,
    category: Category,
    category_data: CategoryUpdate,
) -> Category:
    update_data = category_data.model_dump(
        exclude_unset=True,
    )

    for field, value in update_data.items():
        setattr(category, field, value)

    db.commit()
    db.refresh(category)

    return category


def delete_category(
    db: Session,
    category: Category,
) -> None:
    db.delete(category)
    db.commit()