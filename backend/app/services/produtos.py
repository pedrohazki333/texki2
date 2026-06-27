from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.produto import Produto
from app.schemas.produto import ProdutoIn, ProdutoUpdate


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
    db.delete(produto)
    db.commit()
