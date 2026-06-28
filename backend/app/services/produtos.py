from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.item_pedido import ItemPedido
from app.models.produto import Produto
from app.schemas.produto import ProdutoIn, ProdutoUpdate


def _tem_itens(db: Session, produto_id: int) -> bool:
    return (
        db.scalar(
            select(ItemPedido.id).where(ItemPedido.produto_id == produto_id).limit(1)
        )
        is not None
    )


def listar(db: Session) -> list[Produto]:
    return list(db.scalars(select(Produto).order_by(Produto.nome)))


def obter(db: Session, produto_id: int) -> Produto | None:
    return db.get(Produto, produto_id)


def criar(db: Session, payload: ProdutoIn) -> Produto:
    produto = Produto(nome=payload.nome, tipo=payload.tipo)
    db.add(produto)
    db.commit()
    db.refresh(produto)
    return produto


def atualizar_nome(db: Session, produto: Produto, payload: ProdutoUpdate) -> Produto:
    produto.nome = payload.nome
    db.commit()
    db.refresh(produto)
    return produto


def excluir(db: Session, produto: Produto) -> None:
    if _tem_itens(db, produto.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "produto.tem_itens",
                "message": (
                    "Produto possui itens em pedidos e não pode ser excluído."
                ),
            },
        )
    db.delete(produto)
    db.commit()
