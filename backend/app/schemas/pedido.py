from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.cliente import ClienteOut

PedidoStatus = Literal[
    "recebido",
    "pago",
    "na_fila_de_impressao",
    "impressao_pronta",
    "pedido_pronto",
    "entregue",
    "cancelado",
]


class ItemPedidoIn(BaseModel):
    produto_id: int
    variacao_id: int | None = None
    quantidade: Decimal = Field(gt=0)


class PedidoIn(BaseModel):
    cliente_id: int
    data_entrega: date
    itens: list[ItemPedidoIn] = Field(min_length=1)


class PedidoUpdate(PedidoIn):
    pass


class ItemPedidoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    produto_id: int
    variacao_id: int | None
    quantidade: Decimal
    preco_unitario: Decimal
    subtotal: Decimal


class ArteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    arquivo_mime: str
    largura_cm: Decimal
    altura_cm: Decimal
    observacoes: str | None
    ordem: int


class PedidoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cliente_id: int
    vendedora_id: int
    status: PedidoStatus
    data_entrega: date
    total: Decimal
    created_at: datetime


class PedidoDetalhesOut(PedidoOut):
    itens: list[ItemPedidoOut]
    artes: list[ArteOut]
    cliente: ClienteOut


class TrocarResponsavelIn(BaseModel):
    vendedora_id: int
