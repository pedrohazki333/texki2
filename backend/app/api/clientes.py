from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_role
from app.schemas.cliente import ClienteIn, ClienteOut, ClienteUpdate
from app.services import clientes as svc

router = APIRouter(dependencies=[Depends(require_role("vendedora", "administrador"))])


def _nao_encontrado() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"code": "cliente.not_found", "message": "Cliente não encontrado."},
    )


@router.get("", response_model=list[ClienteOut])
def listar(db: Session = Depends(get_db)) -> list[ClienteOut]:
    return [ClienteOut.model_validate(c) for c in svc.listar(db)]


@router.post("", response_model=ClienteOut, status_code=status.HTTP_201_CREATED)
def criar(payload: ClienteIn, db: Session = Depends(get_db)) -> ClienteOut:
    return ClienteOut.model_validate(svc.criar(db, payload))


@router.get("/{cliente_id}", response_model=ClienteOut)
def obter(cliente_id: int, db: Session = Depends(get_db)) -> ClienteOut:
    cliente = svc.obter(db, cliente_id)
    if cliente is None:
        raise _nao_encontrado()
    return ClienteOut.model_validate(cliente)


@router.put("/{cliente_id}", response_model=ClienteOut)
def atualizar(
    cliente_id: int, payload: ClienteUpdate, db: Session = Depends(get_db)
) -> ClienteOut:
    cliente = svc.obter(db, cliente_id)
    if cliente is None:
        raise _nao_encontrado()
    return ClienteOut.model_validate(svc.atualizar(db, cliente, payload))


@router.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(cliente_id: int, db: Session = Depends(get_db)) -> Response:
    cliente = svc.obter(db, cliente_id)
    if cliente is None:
        raise _nao_encontrado()
    svc.excluir(db, cliente)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{cliente_id}/anonimizar", response_model=ClienteOut)
def anonimizar(cliente_id: int, db: Session = Depends(get_db)) -> ClienteOut:
    cliente = svc.obter(db, cliente_id)
    if cliente is None:
        raise _nao_encontrado()
    return ClienteOut.model_validate(svc.anonimizar(db, cliente))
