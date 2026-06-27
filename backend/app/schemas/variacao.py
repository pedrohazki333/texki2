from pydantic import BaseModel, ConfigDict, Field


class VariacaoIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    cor: str = Field(min_length=1, max_length=60)
    tamanho: str = Field(min_length=1, max_length=20)


class VariacaoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cor: str
    tamanho: str
