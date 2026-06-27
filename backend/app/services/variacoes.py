from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.produto import Produto
from app.models.variacao import Variacao
from app.schemas.variacao import VariacaoIn


def _erro_tipo_invalido() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={
            "code": "variacao.tipo_invalido",
            "message": "Variações só podem ser cadastradas em produtos de vestuário.",
        },
    )


def _erro_duplicada() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={
            "code": "variacao.duplicada",
            "message": "Já existe uma variação com essa cor e tamanho neste produto.",
        },
    )


def obter(db: Session, variacao_id: int) -> Variacao | None:
    return db.get(Variacao, variacao_id)


def criar(db: Session, produto: Produto, payload: VariacaoIn) -> Variacao:
    if produto.tipo != "vestuario":
        raise _erro_tipo_invalido()
    variacao = Variacao(produto_id=produto.id, cor=payload.cor, tamanho=payload.tamanho)
    db.add(variacao)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise _erro_duplicada()
    db.refresh(variacao)
    return variacao


def atualizar(db: Session, variacao: Variacao, payload: VariacaoIn) -> Variacao:
    variacao.cor = payload.cor
    variacao.tamanho = payload.tamanho
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise _erro_duplicada()
    db.refresh(variacao)
    return variacao


def excluir(db: Session, variacao: Variacao) -> None:
    db.delete(variacao)
    db.commit()
