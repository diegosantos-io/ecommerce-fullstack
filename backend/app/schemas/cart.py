from datetime import datetime

from pydantic import BaseModel, Field


class CartItemCreate(BaseModel):
    produto_id: int = Field(
        gt=0,
    )

    quantidade: int = Field(
        gt=0,
    )


class CartItemUpdate(BaseModel):
    quantidade: int = Field(
        gt=0,
    )


class CartItemResponse(BaseModel):
    id: int
    produto_id: int
    quantidade: int

    model_config = {
        "from_attributes": True
    }


class CartResponse(BaseModel):
    id: int
    usuario_id: int
    itens: list[CartItemResponse]
    criado_em: datetime
    atualizado_em: datetime