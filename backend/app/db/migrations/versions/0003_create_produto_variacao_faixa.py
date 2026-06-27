"""create produto, variacao, faixa_preco

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-27

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "produto",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("nome", sa.String(120), nullable=False),
        sa.Column(
            "tipo",
            sa.Enum("dtf_por_metro", "vestuario", name="produto_tipo"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "variacao",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "produto_id",
            sa.BigInteger(),
            sa.ForeignKey("produto.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("cor", sa.String(60), nullable=False),
        sa.Column("tamanho", sa.String(20), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "produto_id",
            "cor",
            "tamanho",
            name="uq_variacao_produto_cor_tamanho",
        ),
    )
    op.create_index("ix_variacao_produto_id", "variacao", ["produto_id"])

    op.create_table(
        "faixa_preco",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "produto_id",
            sa.BigInteger(),
            sa.ForeignKey("produto.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "base",
            sa.Enum("comprimento_m", "quantidade", name="faixa_base"),
            nullable=False,
        ),
        sa.Column("min", sa.Numeric(10, 2), nullable=False),
        sa.Column("max", sa.Numeric(10, 2), nullable=True),
        sa.Column("preco_unitario", sa.Numeric(10, 2), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            '"max" IS NULL OR "min" < "max"', name="ck_faixa_preco_min_max"
        ),
        sa.CheckConstraint(
            "preco_unitario > 0", name="ck_faixa_preco_preco_positivo"
        ),
    )
    op.create_index("ix_faixa_preco_produto_id", "faixa_preco", ["produto_id"])


def downgrade() -> None:
    op.drop_index("ix_faixa_preco_produto_id", table_name="faixa_preco")
    op.drop_table("faixa_preco")
    op.drop_index("ix_variacao_produto_id", table_name="variacao")
    op.drop_table("variacao")
    op.drop_table("produto")
    sa.Enum(name="faixa_base").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="produto_tipo").drop(op.get_bind(), checkfirst=True)
