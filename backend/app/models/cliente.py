from datetime import date, datetime

from sqlalchemy import BigInteger, Boolean, Date, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Cliente(Base):
    __tablename__ = "cliente"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    primeiro_nome: Mapped[str] = mapped_column(String(120), nullable=False)
    ultimo_nome: Mapped[str | None] = mapped_column(String(120), nullable=True)
    endereco: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telefone: Mapped[str] = mapped_column(String(40), nullable=False)
    consentimento_lgpd: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    data_consentimento: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
