from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate
from app.utils.password import hash_password, verify_password


def get_user_by_email(
    db: Session,
    email: str,
) -> User | None:
    return (
        db.query(User)
        .filter(User.email == email)
        .first()
    )


def create_user(
    db: Session,
    user_data: UserCreate,
) -> User:
    senha_hash = hash_password(user_data.senha)

    user = User(
        nome=user_data.nome,
        email=user_data.email,
        senha_hash=senha_hash,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def authenticate_user(
        db:Session,
        email: str,
        senha: str,
) -> User | None:
    user = get_user_by_email(db, email)

    if not user: 
        return None

    if not verify_password(senha,user.senha_hash):
        return None

    if not user.ativo:
        return None

    return user