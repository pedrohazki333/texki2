from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

BaseFaixa = Literal["comprimento_m", "quantidade"]


class FaixaPrecoIn(BaseModel):
    base: BaseFaixa
    min: Decimal = Field(ge=0)
    max: Decimal | None = Field(default=None, gt=0)
    preco_unitario: Decimal = Field(gt=0)

    @model_validator(mode="after")
    def validar_min_menor_que_max(self):
        if self.max is not None and self.min >= self.max:
            raise ValueError("min deve ser menor que max")
        return self


class FaixaPrecoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    base: BaseFaixa
    min: Decimal
    max: Decimal | None
    preco_unitario: Decimal


class PrecoSelecionadoOut(BaseModel):
    faixa_id: int
    preco_unitario: Decimal
