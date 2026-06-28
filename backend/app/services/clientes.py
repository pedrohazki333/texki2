from datetime import date, datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.cliente import Cliente
from app.models.pedido import Pedido
from app.schemas.cliente import ClienteIn, ClienteUpdate

ANONIMIZADO_NOME = "(cliente anonimizado)"
ANONIMIZADO_TEL = "(removido)"


def _hoje_utc() -> date:
    return datetime.now(timezone.utc).date()


def _tem_pedidos(db: Session, cliente_id: int) -> bool:
    return (
        db.scalar(select(Pedido.id).where(Pedido.cliente_id == cliente_id).limit(1))
        is not None
    )


def listar(db: Session) -> list[Cliente]:
    stmt = select(Cliente).order_by(Cliente.primeiro_nome, Cliente.ultimo_nome)
    return list(db.scalars(stmt))


def obter(db: Session, cliente_id: int) -> Cliente | None:
    return db.get(Cliente, cliente_id)


def criar(db: Session, payload: ClienteIn) -> Cliente:
    cliente = Cliente(
        primeiro_nome=payload.primeiro_nome,
        ultimo_nome=payload.ultimo_nome,
        endereco=payload.endereco,
        telefone=payload.telefone,
        consentimento_lgpd=payload.consentimento_lgpd,
        data_consentimento=_hoje_utc() if payload.consentimento_lgpd else None,
    )
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return cliente


def atualizar(db: Session, cliente: Cliente, payload: ClienteUpdate) -> Cliente:
    cliente.primeiro_nome = payload.primeiro_nome
    cliente.ultimo_nome = payload.ultimo_nome
    cliente.endereco = payload.endereco
    cliente.telefone = payload.telefone

    # Triagem do consentimento por transição (não por estado):
    # editar um cliente já consentido NÃO reseta data_consentimento — preserva
    # a data original do consentimento. Só a transição false→true grava hoje.
    if not payload.consentimento_lgpd:
        cliente.data_consentimento = None
    elif cliente.data_consentimento is None:
        cliente.data_consentimento = _hoje_utc()
    cliente.consentimento_lgpd = payload.consentimento_lgpd

    db.commit()
    db.refresh(cliente)
    return cliente


def excluir(db: Session, cliente: Cliente) -> None:
    if _tem_pedidos(db, cliente.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "cliente.tem_pedidos",
                "message": (
                    "Cliente possui pedidos vinculados. Para o esquecimento (LGPD), "
                    "use 'anonimizar' em vez de excluir."
                ),
            },
        )
    db.delete(cliente)
    db.commit()


def anonimizar(db: Session, cliente: Cliente) -> Cliente:
    """Zera dados pessoais mantendo o registro (LGPD, art. 16). Não toca pedidos."""
    cliente.primeiro_nome = ANONIMIZADO_NOME
    cliente.ultimo_nome = None
    cliente.endereco = None
    cliente.telefone = ANONIMIZADO_TEL
    cliente.consentimento_lgpd = False
    cliente.data_consentimento = None
    db.commit()
    db.refresh(cliente)
    return cliente
