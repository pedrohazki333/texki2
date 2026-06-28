"""Testes do service de proporção (RF5 / minispec).

Cobre: leitura de PNG recortando a transparência, arredondamento a 1mm,
âncora do cadeado e validação das medidas casando com a proporção.
"""
import io
from decimal import Decimal

import pytest
from PIL import Image

from app.services import proportion as svc


def _png_bytes_com_bbox(largura_px: int, altura_px: int, padding: int = 0) -> bytes:
    """Gera PNG totalmente transparente exceto por um retângulo opaco de
    `largura_px` × `altura_px` no canto, com `padding` em volta. A proporção
    do bbox real é largura_px / altura_px (independente do padding)."""
    canvas_w = largura_px + padding * 2
    canvas_h = altura_px + padding * 2
    img = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    # bloco opaco (vermelho 100%)
    for x in range(padding, padding + largura_px):
        for y in range(padding, padding + altura_px):
            img.putpixel((x, y), (255, 0, 0, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_ler_proporcao_png_simples():
    dados = _png_bytes_com_bbox(200, 100)
    proporcao = svc.ler_proporcao_png(io.BytesIO(dados))
    assert proporcao == Decimal("2")


def test_ler_proporcao_png_recorta_transparencia():
    """200×100 cercado por 50px de transparência → bbox = 200×100 → proporção 2."""
    dados = _png_bytes_com_bbox(200, 100, padding=50)
    proporcao = svc.ler_proporcao_png(io.BytesIO(dados))
    assert proporcao == Decimal("2")


def test_ler_proporcao_png_todo_transparente_falha():
    img = Image.new("RGBA", (20, 20), (0, 0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    with pytest.raises(Exception):
        svc.ler_proporcao_png(io.BytesIO(buf.getvalue()))


def test_corrigir_medidas_ancorando_largura():
    # proporção 2: largura 30 ancora → altura 15
    largura, altura = svc.corrigir_medidas(
        Decimal("2"), Decimal("30"), Decimal("99"), "largura"
    )
    assert largura == Decimal("30")
    assert altura == Decimal("15.0")


def test_corrigir_medidas_ancorando_altura():
    # proporção 2: altura 20 ancora → largura 40
    largura, altura = svc.corrigir_medidas(
        Decimal("2"), Decimal("99"), Decimal("20"), "altura"
    )
    assert largura == Decimal("40.0")
    assert altura == Decimal("20")


def test_corrigir_medidas_arredonda_a_milimetro():
    # proporção 1.73 com largura 30 → altura 17.34… → 17.3 cm
    largura, altura = svc.corrigir_medidas(
        Decimal("1.73"), Decimal("30"), Decimal("99"), "largura"
    )
    assert altura == Decimal("17.3")


def test_medidas_batem_com_proporcao_caso_basico():
    # proporção 2 com 30×15 → bate.
    assert svc.medidas_batem_com_proporcao(Decimal("2"), Decimal("30"), Decimal("15"))


def test_medidas_batem_com_proporcao_aceita_arredondamento_de_mm():
    # proporção 1.73, largura 30, altura 17.3 (arredondada do 17.341…) → bate.
    assert svc.medidas_batem_com_proporcao(
        Decimal("1.73"), Decimal("30"), Decimal("17.3")
    )


def test_medidas_nao_batem_com_proporcao():
    # proporção 2 com 30×20 → divergente.
    assert not svc.medidas_batem_com_proporcao(
        Decimal("2"), Decimal("30"), Decimal("20")
    )


def test_medidas_zero_nao_passam():
    assert not svc.medidas_batem_com_proporcao(
        Decimal("2"), Decimal("0"), Decimal("10")
    )
