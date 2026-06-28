"""Camada única de acesso a arquivos (ADR-0002).

Tudo que toca arquivo passa por aqui — assim, trocar filesystem por storage
de objetos depois é uma alteração local. Não importe `os.path`/`open` no
restante do código.
"""
from __future__ import annotations

import uuid
from pathlib import Path
from typing import BinaryIO

from fastapi import HTTPException, status

from app.core.config import settings

# Tipos aceitos (RNF1).
EXT_POR_MIME: dict[str, str] = {
    "image/png": ".png",
    "application/pdf": ".pdf",
    "image/tiff": ".tiff",
}

# Limite de 25 MB (RNF1).
TAMANHO_MAXIMO_BYTES = 25 * 1024 * 1024


def _base_dir() -> Path:
    base = Path(settings.uploads_dir)
    base.mkdir(parents=True, exist_ok=True)
    return base


def _erro_arquivo_invalido(message: str, code: str = "arte.arquivo_invalido") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={"code": code, "message": message},
    )


def validar_mime(content_type: str | None) -> str:
    if content_type not in EXT_POR_MIME:
        raise _erro_arquivo_invalido(
            "Formato não aceito. Use PNG, PDF ou TIFF.",
            code="arte.formato_invalido",
        )
    return content_type


def salvar(stream: BinaryIO, *, content_type: str, tamanho: int | None = None) -> str:
    """Salva o stream e devolve o caminho RELATIVO (ex.: 'abc.png')."""
    mime = validar_mime(content_type)
    dados = stream.read()
    if len(dados) > TAMANHO_MAXIMO_BYTES:
        raise _erro_arquivo_invalido(
            "Arquivo maior que 25 MB.", code="arte.tamanho_excedido"
        )
    if tamanho is not None and tamanho != len(dados):
        # confiamos no que está no disco — apenas validamos limites
        pass
    nome = f"{uuid.uuid4().hex}{EXT_POR_MIME[mime]}"
    caminho_abs = _base_dir() / nome
    caminho_abs.write_bytes(dados)
    return nome


def caminho_absoluto(relativo: str) -> Path:
    p = (_base_dir() / relativo).resolve()
    base = _base_dir().resolve()
    # protege contra escape do diretório base (../).
    if base not in p.parents and p != base:
        raise _erro_arquivo_invalido("Caminho inválido.")
    return p


def remover(relativo: str) -> None:
    p = caminho_absoluto(relativo)
    if p.exists():
        p.unlink()
