"""arte: coluna quantidade (peças que recebem esta arte)

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-28

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "arte",
        sa.Column("quantidade", sa.Integer(), nullable=False, server_default="1"),
    )
    op.create_check_constraint(
        "ck_arte_quantidade_positiva", "arte", "quantidade > 0"
    )


def downgrade() -> None:
    op.drop_constraint("ck_arte_quantidade_positiva", "arte", type_="check")
    op.drop_column("arte", "quantidade")
