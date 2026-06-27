from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.produto import Produto


class Variacao(Base):
    __tablename__ = "variacao"
    __table_args__ = (
        UniqueConstraint(
            "produto_id",
            "cor",
            "tamanho",
            name="uq_variacao_produto_cor_tamanho",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    produto_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("produto.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    cor: Mapped[str] = mapped_column(String(60), nullable=False)
    tamanho: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    produto: Mapped["Produto"] = relationship(back_populates="variacoes")
