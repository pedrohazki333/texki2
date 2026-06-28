from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.pedido import Pedido
    from app.models.produto import Produto
    from app.models.variacao import Variacao


class ItemPedido(Base):
    __tablename__ = "item_pedido"
    __table_args__ = (
        CheckConstraint("quantidade > 0", name="ck_item_pedido_quantidade_positiva"),
        CheckConstraint("preco_unitario > 0", name="ck_item_pedido_preco_positivo"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    pedido_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("pedido.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    produto_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("produto.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    variacao_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("variacao.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    quantidade: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    preco_unitario: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    pedido: Mapped["Pedido"] = relationship(back_populates="itens")
    produto: Mapped["Produto"] = relationship()
    variacao: Mapped["Variacao | None"] = relationship()
