from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class OrderItemResponse(BaseModel):
    id: int
    produto_id: int
    quantidade: int
    preco_unitario: Decimal
    subtotal: Decimal

    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    id: int
    usuario_id: int
    status: str
    subtotal: Decimal
    frete: Decimal
    total: Decimal
    itens: list[OrderItemResponse]
    criado_em: datetime
    atualizado_em: datetime