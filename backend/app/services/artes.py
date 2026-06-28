from __future__ import annotations

import io
from decimal import Decimal

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.arte import Arte
from app.models.pedido import Pedido
from app.services import proportion as prop_svc
from app.storage import validar_mime, salvar, remover


def _ler_para_buffer(upload: UploadFile) -> bytes:
    dados = upload.file.read()
    upload.file.seek(0)
    return dados


def _proxima_ordem(db: Session, pedido_id: int) -> int:
    atual = db.scalar(
        select(func.coalesce(func.max(Arte.ordem), 0)).where(Arte.pedido_id == pedido_id)
    )
    return int(atual or 0) + 1


def analisar(upload: UploadFile) -> dict:
    """Recebe um arquivo e devolve proporção (se PNG) — sem persistir nada."""
    mime = validar_mime(upload.content_type)
    if mime == "image/png":
        dados = _ler_para_buffer(upload)
        proporcao = prop_svc.ler_proporcao_png(io.BytesIO(dados))
        return {"mime": mime, "proporcao": str(proporcao), "cadeado": "fechado"}
    return {"mime": mime, "proporcao": None, "cadeado": "aberto"}


def criar(
    db: Session,
    pedido: Pedido,
    *,
    upload: UploadFile,
    largura_cm: Decimal,
    altura_cm: Decimal,
    quantidade: int,
    observacoes: str | None,
) -> Arte:
    mime = validar_mime(upload.content_type)
    if largura_cm <= 0 or altura_cm <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "arte.medidas_invalidas",
                "message": "Largura e altura devem ser positivas.",
            },
        )
    if quantidade <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "arte.quantidade_invalida",
                "message": "A quantidade de peças com esta arte precisa ser ≥ 1.",
            },
        )
    dados = _ler_para_buffer(upload)
    if mime == "image/png":
        proporcao = prop_svc.ler_proporcao_png(io.BytesIO(dados))
        if not prop_svc.medidas_batem_com_proporcao(proporcao, largura_cm, altura_cm):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": "arte.proporcao_divergente",
                    "message": (
                        "As medidas informadas não batem com a proporção da arte. "
                        "Com o cadeado fechado, edite só uma das medidas."
                    ),
                },
            )
    caminho = salvar(io.BytesIO(dados), content_type=mime)
    arte = Arte(
        pedido_id=pedido.id,
        arquivo_path=caminho,
        arquivo_mime=mime,
        largura_cm=largura_cm,
        altura_cm=altura_cm,
        quantidade=quantidade,
        observacoes=observacoes or None,
        ordem=_proxima_ordem(db, pedido.id),
    )
    db.add(arte)
    db.commit()
    db.refresh(arte)
    return arte


def obter(db: Session, pedido_id: int, arte_id: int) -> Arte | None:
    return db.scalar(
        select(Arte).where(Arte.id == arte_id, Arte.pedido_id == pedido_id)
    )


def excluir(db: Session, arte: Arte) -> None:
    caminho = arte.arquivo_path
    db.delete(arte)
    db.commit()
    # remove o arquivo só depois do commit ter ido bem
    remover(caminho)
