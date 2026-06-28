from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.arte import Arte
    from app.models.cliente import Cliente
    from app.models.item_pedido import ItemPedido
    from app.models.usuario import Usuario


class Pedido(Base):
    __tablename__ = "pedido"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    cliente_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("cliente.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    vendedora_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("usuario.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        Enum(
            "recebido",
            "pago",
            "na_fila_de_impressao",
            "impressao_pronta",
            "pedido_pronto",
            "entregue",
            "cancelado",
            name="pedido_status",
        ),
        nullable=False,
        default="recebido",
        server_default="recebido",
        index=True,
    )
    data_entrega: Mapped[date] = mapped_column(Date, nullable=False)
    total: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0"), server_default="0"
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

    cliente: Mapped["Cliente"] = relationship()
    vendedora: Mapped["Usuario"] = relationship()
    itens: Mapped[list["ItemPedido"]] = relationship(
        back_populates="pedido",
        cascade="all, delete-orphan",
        order_by="ItemPedido.id",
    )
    artes: Mapped[list["Arte"]] = relationship(
        back_populates="pedido",
        cascade="all, delete-orphan",
        order_by="Arte.ordem",
    )
