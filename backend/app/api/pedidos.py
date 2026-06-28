from decimal import Decimal, InvalidOperation

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Response,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_role
from app.models.pedido import Pedido
from app.models.usuario import Usuario
from app.schemas.pedido import (
    ArteOut,
    PedidoDetalhesOut,
    PedidoIn,
    PedidoOut,
    PedidoUpdate,
    TrocarResponsavelIn,
)
from app.services import artes as artes_svc
from app.services import pedidos as svc
from app.storage import caminho_absoluto

router = APIRouter()


def _nao_encontrado() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"code": "pedido.not_found", "message": "Pedido não encontrado."},
    )


def _obter_ou_404(db: Session, pedido_id: int) -> Pedido:
    pedido = svc.obter(db, pedido_id)
    if pedido is None:
        raise _nao_encontrado()
    return pedido


# ---- rotas literais antes das paramétricas (evita conflito de matching) ----

@router.get(
    "/_utils/vendedoras",
    response_model=list[dict],
    dependencies=[Depends(get_current_user)],
)
def listar_responsaveis_possiveis(db: Session = Depends(get_db)) -> list[dict]:
    stmt = (
        select(Usuario)
        .where(
            Usuario.role.in_(["vendedora", "administrador"]),
            Usuario.ativo.is_(True),
        )
        .order_by(Usuario.nome)
    )
    return [{"id": u.id, "nome": u.nome, "role": u.role} for u in db.scalars(stmt)]


# ---- CRUD ----

@router.get(
    "",
    response_model=list[PedidoOut],
    dependencies=[Depends(require_role("vendedora", "administrador"))],
)
def listar(db: Session = Depends(get_db)) -> list[PedidoOut]:
    return [PedidoOut.model_validate(p) for p in svc.listar(db)]


@router.post(
    "",
    response_model=PedidoDetalhesOut,
    status_code=status.HTTP_201_CREATED,
)
def criar(
    payload: PedidoIn,
    db: Session = Depends(get_db),
    user: Usuario = Depends(require_role("vendedora", "administrador")),
) -> PedidoDetalhesOut:
    pedido = svc.criar(db, payload, user)
    return PedidoDetalhesOut.model_validate(pedido)


@router.get(
    "/{pedido_id}",
    response_model=PedidoDetalhesOut,
    dependencies=[Depends(require_role("vendedora", "administrador"))],
)
def obter(pedido_id: int, db: Session = Depends(get_db)) -> PedidoDetalhesOut:
    return PedidoDetalhesOut.model_validate(_obter_ou_404(db, pedido_id))


@router.put(
    "/{pedido_id}",
    response_model=PedidoDetalhesOut,
    dependencies=[Depends(require_role("vendedora", "administrador"))],
)
def atualizar(
    pedido_id: int,
    payload: PedidoUpdate,
    db: Session = Depends(get_db),
) -> PedidoDetalhesOut:
    pedido = _obter_ou_404(db, pedido_id)
    return PedidoDetalhesOut.model_validate(svc.atualizar(db, pedido, payload))


@router.delete(
    "/{pedido_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role("vendedora", "administrador"))],
)
def excluir(pedido_id: int, db: Session = Depends(get_db)) -> Response:
    pedido = _obter_ou_404(db, pedido_id)
    svc.excluir(db, pedido)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put(
    "/{pedido_id}/responsavel",
    response_model=PedidoDetalhesOut,
)
def trocar_responsavel(
    pedido_id: int,
    payload: TrocarResponsavelIn,
    db: Session = Depends(get_db),
    # Só administrador pode trocar o responsável de um pedido.
    user: Usuario = Depends(require_role("administrador")),
) -> PedidoDetalhesOut:
    pedido = _obter_ou_404(db, pedido_id)
    return PedidoDetalhesOut.model_validate(
        svc.trocar_responsavel(db, pedido, payload.vendedora_id, user)
    )


# ---- artes (RF5 / 3b) ----

def _parse_decimal(nome: str, valor: str) -> Decimal:
    try:
        return Decimal(valor)
    except (InvalidOperation, ValueError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "arte.medida_nao_numerica",
                "message": f"O campo '{nome}' precisa ser numérico.",
            },
        )


@router.post(
    "/{pedido_id}/artes/analisar",
    dependencies=[Depends(require_role("vendedora", "administrador"))],
)
def analisar_arte(
    pedido_id: int,
    arquivo: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict:
    _obter_ou_404(db, pedido_id)
    return artes_svc.analisar(arquivo)


@router.post(
    "/{pedido_id}/artes",
    response_model=ArteOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("vendedora", "administrador"))],
)
def criar_arte(
    pedido_id: int,
    arquivo: UploadFile = File(...),
    largura_cm: str = Form(...),
    altura_cm: str = Form(...),
    observacoes: str | None = Form(default=None),
    db: Session = Depends(get_db),
) -> ArteOut:
    pedido = _obter_ou_404(db, pedido_id)
    arte = artes_svc.criar(
        db,
        pedido,
        upload=arquivo,
        largura_cm=_parse_decimal("largura_cm", largura_cm),
        altura_cm=_parse_decimal("altura_cm", altura_cm),
        observacoes=observacoes,
    )
    return ArteOut.model_validate(arte)


@router.get(
    "/{pedido_id}/artes/{arte_id}/arquivo",
    dependencies=[Depends(require_role("vendedora", "impressor", "administrador"))],
)
def baixar_arquivo_arte(
    pedido_id: int, arte_id: int, db: Session = Depends(get_db)
) -> FileResponse:
    arte = artes_svc.obter(db, pedido_id, arte_id)
    if arte is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "arte.not_found", "message": "Arte não encontrada."},
        )
    return FileResponse(
        path=caminho_absoluto(arte.arquivo_path),
        media_type=arte.arquivo_mime,
        filename=arte.arquivo_path,
    )


@router.delete(
    "/{pedido_id}/artes/{arte_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role("vendedora", "administrador"))],
)
def excluir_arte(
    pedido_id: int, arte_id: int, db: Session = Depends(get_db)
) -> Response:
    arte = artes_svc.obter(db, pedido_id, arte_id)
    if arte is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "arte.not_found", "message": "Arte não encontrada."},
        )
    artes_svc.excluir(db, arte)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
