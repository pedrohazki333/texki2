from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.pedido import Pedido


class Arte(Base):
    __tablename__ = "arte"
    __table_args__ = (
        CheckConstraint("largura_cm > 0", name="ck_arte_largura_positiva"),
        CheckConstraint("altura_cm > 0", name="ck_arte_altura_positiva"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    pedido_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("pedido.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    arquivo_path: Mapped[str] = mapped_column(String(255), nullable=False)
    arquivo_mime: Mapped[str] = mapped_column(String(80), nullable=False)
    largura_cm: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    altura_cm: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
    ordem: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    pedido: Mapped["Pedido"] = relationship(back_populates="artes")
