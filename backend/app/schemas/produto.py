from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.faixa_preco import FaixaPrecoOut
from app.schemas.variacao import VariacaoOut

TipoProduto = Literal["dtf_por_metro", "vestuario"]


class ProdutoIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nome: str = Field(min_length=1, max_length=120)
    tipo: TipoProduto


class ProdutoUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nome: str = Field(min_length=1, max_length=120)


class ProdutoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    tipo: TipoProduto


class ProdutoDetalhesOut(ProdutoOut):
    variacoes: list[VariacaoOut]
    faixas: list[FaixaPrecoOut]
