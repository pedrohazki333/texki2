"""create pedido, item_pedido, arte, auditoria

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-28

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "pedido",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "cliente_id",
            sa.BigInteger(),
            # RESTRICT: cliente com pedidos não é excluído direto (oferece-se anonimização — LGPD).
            sa.ForeignKey("cliente.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "vendedora_id",
            sa.BigInteger(),
            sa.ForeignKey("usuario.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
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
            server_default="recebido",
        ),
        sa.Column("data_entrega", sa.Date(), nullable=False),
        sa.Column(
            "total",
            sa.Numeric(10, 2),
            nullable=False,
            server_default="0",
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
    op.create_index("ix_pedido_cliente_id", "pedido", ["cliente_id"])
    op.create_index("ix_pedido_vendedora_id", "pedido", ["vendedora_id"])
    op.create_index("ix_pedido_status", "pedido", ["status"])

    op.create_table(
        "item_pedido",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "pedido_id",
            sa.BigInteger(),
            sa.ForeignKey("pedido.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "produto_id",
            sa.BigInteger(),
            # RESTRICT: produto com itens não pode ser excluído.
            sa.ForeignKey("produto.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "variacao_id",
            sa.BigInteger(),
            sa.ForeignKey("variacao.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("quantidade", sa.Numeric(10, 2), nullable=False),
        sa.Column("preco_unitario", sa.Numeric(10, 2), nullable=False),
        sa.Column("subtotal", sa.Numeric(10, 2), nullable=False),
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
        sa.CheckConstraint("quantidade > 0", name="ck_item_pedido_quantidade_positiva"),
        sa.CheckConstraint("preco_unitario > 0", name="ck_item_pedido_preco_positivo"),
    )
    op.create_index("ix_item_pedido_pedido_id", "item_pedido", ["pedido_id"])
    op.create_index("ix_item_pedido_produto_id", "item_pedido", ["produto_id"])
    op.create_index("ix_item_pedido_variacao_id", "item_pedido", ["variacao_id"])

    op.create_table(
        "arte",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "pedido_id",
            sa.BigInteger(),
            sa.ForeignKey("pedido.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("arquivo_path", sa.String(255), nullable=False),
        sa.Column("arquivo_mime", sa.String(80), nullable=False),
        sa.Column("largura_cm", sa.Numeric(10, 2), nullable=False),
        sa.Column("altura_cm", sa.Numeric(10, 2), nullable=False),
        sa.Column("observacoes", sa.Text(), nullable=True),
        sa.Column("ordem", sa.Integer(), nullable=False),
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
        sa.CheckConstraint("largura_cm > 0", name="ck_arte_largura_positiva"),
        sa.CheckConstraint("altura_cm > 0", name="ck_arte_altura_positiva"),
    )
    op.create_index("ix_arte_pedido_id", "arte", ["pedido_id"])

    op.create_table(
        "auditoria",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "usuario_id",
            sa.BigInteger(),
            sa.ForeignKey("usuario.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("entidade", sa.String(60), nullable=False),
        sa.Column("entidade_id", sa.BigInteger(), nullable=False),
        sa.Column("campo", sa.String(60), nullable=False),
        sa.Column("valor_anterior", sa.Text(), nullable=True),
        sa.Column("valor_novo", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_auditoria_entidade", "auditoria", ["entidade", "entidade_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_auditoria_entidade", table_name="auditoria")
    op.drop_table("auditoria")

    op.drop_index("ix_arte_pedido_id", table_name="arte")
    op.drop_table("arte")

    op.drop_index("ix_item_pedido_variacao_id", table_name="item_pedido")
    op.drop_index("ix_item_pedido_produto_id", table_name="item_pedido")
    op.drop_index("ix_item_pedido_pedido_id", table_name="item_pedido")
    op.drop_table("item_pedido")

    op.drop_index("ix_pedido_status", table_name="pedido")
    op.drop_index("ix_pedido_vendedora_id", table_name="pedido")
    op.drop_index("ix_pedido_cliente_id", table_name="pedido")
    op.drop_table("pedido")
    sa.Enum(name="pedido_status").drop(op.get_bind(), checkfirst=True)
