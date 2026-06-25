"""create cliente

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-25

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cliente",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("primeiro_nome", sa.String(120), nullable=False),
        sa.Column("ultimo_nome", sa.String(120), nullable=True),
        sa.Column("endereco", sa.String(255), nullable=True),
        sa.Column("telefone", sa.String(40), nullable=False),
        sa.Column(
            "consentimento_lgpd",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column("data_consentimento", sa.Date(), nullable=True),
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
    op.create_index("ix_cliente_primeiro_nome", "cliente", ["primeiro_nome"])


def downgrade() -> None:
    op.drop_index("ix_cliente_primeiro_nome", table_name="cliente")
    op.drop_table("cliente")
