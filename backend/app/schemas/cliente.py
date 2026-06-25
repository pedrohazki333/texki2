from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator

TELEFONE_REGEX = r"^\(\d{2}\) \d{4,5}-\d{4}$"


class ClienteIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    primeiro_nome: str = Field(min_length=1, max_length=120)
    ultimo_nome: str | None = Field(default=None, max_length=120)
    endereco: str | None = Field(default=None, max_length=255)
    telefone: str = Field(pattern=TELEFONE_REGEX, description="(XX) XXXX-XXXX ou (XX) XXXXX-XXXX")
    consentimento_lgpd: bool = False

    @field_validator("ultimo_nome", "endereco", mode="before")
    @classmethod
    def vazio_vira_none(cls, v):
        if v is None:
            return None
        if isinstance(v, str) and v.strip() == "":
            return None
        return v


class ClienteUpdate(ClienteIn):
    pass


class ClienteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    primeiro_nome: str
    ultimo_nome: str | None
    endereco: str | None
    telefone: str
    consentimento_lgpd: bool
    data_consentimento: date | None
