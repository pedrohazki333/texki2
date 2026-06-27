from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.faixa_preco import FaixaPreco
    from app.models.variacao import Variacao


class Produto(Base):
    __tablename__ = "produto"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    tipo: Mapped[str] = mapped_column(
        Enum("dtf_por_metro", "vestuario", name="produto_tipo"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    variacoes: Mapped[list["Variacao"]] = relationship(
        back_populates="produto",
        cascade="all, delete-orphan",
        order_by="Variacao.cor, Variacao.tamanho",
    )
    faixas: Mapped[list["FaixaPreco"]] = relationship(
        back_populates="produto",
        cascade="all, delete-orphan",
        order_by="FaixaPreco.min",
    )
