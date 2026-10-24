from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.auth.jwt import create_access_token
from app.auth.dependencies import( 
    get_current_user,
    require_admin
)
from app.models import User

from app.database.database import get_db
from app.schemas.user import(
     UserCreate,
     UserLogin,
     UserResponse,
     TokenResponse,
)

from app.services.user_service import(
    authenticate_user,
    create_user,
    get_user_by_email
)


router = APIRouter(
    prefix = "/usuarios",
    tags = ["Usuários"],
)

@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)

def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    existing_user = get_user_by_email(
        db,
        user_data.email,
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail = "E-mail já cadastrado"
        )

    return create_user(
        db,
        user_data,
    )

@router.post(
    "/login",
    response_model=TokenResponse,
)
def login_user(
    user_data:UserLogin,
    db:Session = Depends(get_db),
):
    user = authenticate_user(
        db,
        user_data.email,
        user_data.senha,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha inválidos.",
        )

    access_token = create_access_token(
        data ={
            "sub": str(user.id),
            "role": user.role,
        }
    )

    return{
        "access_token": access_token,
        "token_type": "bearer",
    }

@router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(
    current_user: User = Depends(get_current_user),
):
    return current_user

@router.get(
    "/admin/teste",
)
def admin_test(
    current_user: User = Depends(require_admin),
):
    return{
        "message": "Acesso administrativo autorizado.",
        "usuario": current_user.nome,
        "role": current_user.role,
    }