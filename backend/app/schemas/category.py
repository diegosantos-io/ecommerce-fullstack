from datetime import datetime

from pydantic import BaseModel, Field

class CategoryCreate(BaseModel):
    nome: str = Field(
        min_length=2,
        max_length=100,
    )

    descricao: str | None = Field(
        default=None,
        max_length=255,
    )

class CategoryUpdate(BaseModel):
    nome: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    descricao: str | None = Field(
        default=None,
        max_length=255,
    )

    ativo: bool | None = None

class CategoryResponse(BaseModel):
    id: int
    nome: str
    descricao: str | None
    ativo: bool
    criado_em: datetime
    atualizado_em: datetime

    model_config = {
        "from_attributes": True
    }