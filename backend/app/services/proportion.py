"""Verificação de proporção da arte (RF5 / minispec).

Resumo do minispec:
- Só PNG lê proporção — leitura recorta o conteúdo não-transparente.
- Tolerância zero; arredondamento da medida corrigida a 1 casa decimal (mm).
- Com cadeado fechado, ancorar na medida digitada primeiro.
- PDF/TIFF não checam.
"""
from __future__ import annotations

import io
from decimal import ROUND_HALF_UP, Decimal
from typing import BinaryIO

from fastapi import HTTPException, status

# Pillow é opcional só para o resto da app — carregamos sob demanda para que
# stubs/tests sem Pillow ainda consigam importar este módulo.
try:
    from PIL import Image
except ImportError:  # pragma: no cover
    Image = None  # type: ignore[assignment]


MM = Decimal("0.1")  # 1 casa decimal (milímetro)


def _erro(code: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={"code": code, "message": message},
    )


def ler_proporcao_png(stream: BinaryIO) -> Decimal:
    """Lê o PNG, recorta a transparência e devolve largura/altura do bbox."""
    if Image is None:  # pragma: no cover
        raise RuntimeError("Pillow não está instalado.")
    dados = stream.read()
    img = Image.open(io.BytesIO(dados))
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    alpha = img.split()[-1]
    bbox = alpha.getbbox()
    if bbox is None:
        # 100% transparente — não dá pra inferir proporção.
        raise _erro(
            "arte.png_sem_conteudo",
            "PNG aparenta estar totalmente transparente — sem conteúdo para medir.",
        )
    largura = Decimal(bbox[2] - bbox[0])
    altura = Decimal(bbox[3] - bbox[1])
    if largura <= 0 or altura <= 0:
        raise _erro("arte.png_invalido", "Não foi possível ler as dimensões do PNG.")
    return largura / altura


def arredondar_mm(valor: Decimal) -> Decimal:
    """Arredonda para 1 casa decimal (mm), meio-acima."""
    return valor.quantize(MM, rounding=ROUND_HALF_UP)


def corrigir_medidas(
    proporcao: Decimal,
    largura: Decimal,
    altura: Decimal,
    ancora: str,
) -> tuple[Decimal, Decimal]:
    """Aplica o cadeado fechado: a medida-âncora manda, a outra é recalculada
    pela proporção, arredondada a 1 casa decimal.

    `ancora` ∈ {"largura", "altura"}.
    """
    if proporcao <= 0:
        raise _erro("arte.proporcao_invalida", "Proporção da arte deve ser positiva.")
    if ancora == "largura":
        nova_altura = arredondar_mm(largura / proporcao)
        return largura, nova_altura
    if ancora == "altura":
        nova_largura = arredondar_mm(altura * proporcao)
        return nova_largura, altura
    raise _erro("arte.ancora_invalida", "Âncora deve ser 'largura' ou 'altura'.")


def medidas_batem_com_proporcao(
    proporcao: Decimal, largura: Decimal, altura: Decimal
) -> bool:
    """As medidas casam com a proporção se forem consistentes pela regra do
    cadeado (com qualquer das duas como âncora) — assim absorvemos o
    arredondamento de mm que o próprio sistema introduz.
    """
    if largura <= 0 or altura <= 0:
        return False
    altura_esperada = arredondar_mm(largura / proporcao)
    if arredondar_mm(altura) == altura_esperada:
        return True
    largura_esperada = arredondar_mm(altura * proporcao)
    return arredondar_mm(largura) == largura_esperada
