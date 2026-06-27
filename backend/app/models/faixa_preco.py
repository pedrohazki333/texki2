from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.produto import Produto


class FaixaPreco(Base):
    __tablename__ = "faixa_preco"
    __table_args__ = (
        CheckConstraint('"max" IS NULL OR "min" < "max"', name="ck_faixa_preco_min_max"),
        CheckConstraint("preco_unitario > 0", name="ck_faixa_preco_preco_positivo"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    produto_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("produto.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    base: Mapped[str] = mapped_column(
        Enum("comprimento_m", "quantidade", name="faixa_base"),
        nullable=False,
    )
    min: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    max: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    preco_unitario: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    produto: Mapped["Produto"] = relationship(back_populates="faixas")
