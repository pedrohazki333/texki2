from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.cliente import Cliente
from app.schemas.cliente import ClienteIn, ClienteUpdate


def _hoje_utc() -> date:
    return datetime.now(timezone.utc).date()


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
    db.delete(cliente)
    db.commit()
