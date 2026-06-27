from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.faixa_preco import FaixaPreco
from app.models.produto import Produto
from app.schemas.faixa_preco import FaixaPrecoIn

BASE_POR_TIPO: dict[str, str] = {
    "dtf_por_metro": "comprimento_m",
    "vestuario": "quantidade",
}


def _erro_base_incompativel(esperada: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={
            "code": "faixa.base_incompativel",
            "message": f"Para este tipo de produto, a base da faixa deve ser '{esperada}'.",
        },
    )


def _erro_sobreposicao() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={
            "code": "faixa.sobreposicao",
            "message": "Já existe uma faixa que cobre essa medida no mesmo produto.",
        },
    )


def _erro_sem_faixa_para_medida() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={
            "code": "preco.sem_faixa_para_medida",
            "message": "Não há faixa cadastrada que cubra essa medida.",
        },
    )


def _sobrepoe(
    a_min: Decimal,
    a_max: Decimal | None,
    b_min: Decimal,
    b_max: Decimal | None,
) -> bool:
    """(a_min, a_max] cruza (b_min, b_max]? max=None significa +infinito."""
    inicio = max(a_min, b_min)
    if a_max is None and b_max is None:
        fim: Decimal | None = None
    elif a_max is None:
        fim = b_max
    elif b_max is None:
        fim = a_max
    else:
        fim = min(a_max, b_max)
    return fim is None or inicio < fim


def obter(db: Session, faixa_id: int) -> FaixaPreco | None:
    return db.get(FaixaPreco, faixa_id)


def _validar_base_e_sobreposicao(
    db: Session,
    produto: Produto,
    payload: FaixaPrecoIn,
    ignorar_id: int | None = None,
) -> None:
    base_esperada = BASE_POR_TIPO[produto.tipo]
    if payload.base != base_esperada:
        raise _erro_base_incompativel(base_esperada)
    existentes = db.scalars(
        select(FaixaPreco).where(FaixaPreco.produto_id == produto.id)
    ).all()
    for f in existentes:
        if ignorar_id is not None and f.id == ignorar_id:
            continue
        if _sobrepoe(payload.min, payload.max, f.min, f.max):
            raise _erro_sobreposicao()


def criar(db: Session, produto: Produto, payload: FaixaPrecoIn) -> FaixaPreco:
    _validar_base_e_sobreposicao(db, produto, payload)
    faixa = FaixaPreco(
        produto_id=produto.id,
        base=payload.base,
        min=payload.min,
        max=payload.max,
        preco_unitario=payload.preco_unitario,
    )
    db.add(faixa)
    db.commit()
    db.refresh(faixa)
    return faixa


def atualizar(
    db: Session, produto: Produto, faixa: FaixaPreco, payload: FaixaPrecoIn
) -> FaixaPreco:
    _validar_base_e_sobreposicao(db, produto, payload, ignorar_id=faixa.id)
    faixa.base = payload.base
    faixa.min = payload.min
    faixa.max = payload.max
    faixa.preco_unitario = payload.preco_unitario
    db.commit()
    db.refresh(faixa)
    return faixa


def excluir(db: Session, faixa: FaixaPreco) -> None:
    db.delete(faixa)
    db.commit()


def selecionar_por_medida(
    db: Session, produto_id: int, medida: Decimal
) -> FaixaPreco:
    """min < medida <= max (max nulo = sem teto). Erro claro se não há faixa."""
    faixa = db.scalar(
        select(FaixaPreco).where(
            FaixaPreco.produto_id == produto_id,
            FaixaPreco.min < medida,
            or_(FaixaPreco.max.is_(None), FaixaPreco.max >= medida),
        )
    )
    if faixa is None:
        raise _erro_sem_faixa_para_medida()
    return faixa
