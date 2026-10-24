from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    nome: str = Field(
        min_length=2,
        max_length=150,
    )

    descricao: str | None = Field(
        default=None,
        max_length=5000,
    )

    preco: Decimal = Field(
        gt=0,
        decimal_places=2,
    )

    estoque: int = Field(
        ge=0,
    )

    imagem_url: str | None = Field(
        default=None,
        max_length=500,
    )

    categoria_id: int = Field(
        gt=0,
    )


class ProductUpdate(BaseModel):
    nome: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    descricao: str | None = Field(
        default=None,
        max_length=5000,
    )

    preco: Decimal | None = Field(
        default=None,
        gt=0,
        decimal_places=2,
    )

    estoque: int | None = Field(
        default=None,
        ge=0,
    )

    imagem_url: str | None = Field(
        default=None,
        max_length=500,
    )

    categoria_id: int | None = Field(
        default=None,
        gt=0,
    )

    ativo: bool | None = None


class ProductResponse(BaseModel):
    id: int
    nome: str
    descricao: str | None
    preco: Decimal
    estoque: int
    imagem_url: str | None
    ativo: bool
    categoria_id: int
    criado_em: datetime
    atualizado_em: datetime

    model_config = {
        "from_attributes": True
    }