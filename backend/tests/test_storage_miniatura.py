"""Geração de miniaturas (RNF4)."""
import io
import time
from pathlib import Path

from PIL import Image

from app.core.config import settings
from app.storage import (
    THUMB_MAX_LADO_PADRAO,
    caminho_miniatura,
    gerar_miniatura,
    salvar,
)


def _png(largura_px: int, altura_px: int) -> io.BytesIO:
    img = Image.new("RGBA", (largura_px, altura_px), (255, 0, 0, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def test_gera_thumb_png_dentro_do_max_lado():
    relativo = salvar(_png(800, 400), content_type="image/png")
    thumb = gerar_miniatura(relativo, mime="image/png")
    assert thumb is not None and thumb.exists()
    with Image.open(thumb) as t:
        w, h = t.size
    assert max(w, h) <= THUMB_MAX_LADO_PADRAO
    # mantém proporção do original (2:1 em ~256:128)
    assert w == THUMB_MAX_LADO_PADRAO
    assert h == THUMB_MAX_LADO_PADRAO // 2


def test_segunda_chamada_nao_regenera():
    relativo = salvar(_png(200, 100), content_type="image/png")
    primeiro = gerar_miniatura(relativo, mime="image/png")
    assert primeiro is not None
    mtime_inicial = primeiro.stat().st_mtime
    time.sleep(0.01)
    segundo = gerar_miniatura(relativo, mime="image/png")
    assert segundo == primeiro
    assert segundo.stat().st_mtime == mtime_inicial


def test_mime_nao_suportado_devolve_none():
    # Não precisa salvar arquivo real; o storage só decide pelo mime.
    Path(settings.uploads_dir, "fake.pdf").write_bytes(b"%PDF-1.4\n%")
    thumb = gerar_miniatura("fake.pdf", mime="application/pdf")
    assert thumb is None
    assert not caminho_miniatura("fake.pdf").exists()


def test_remover_arquivo_remove_thumb_tambem():
    from app.storage import remover

    relativo = salvar(_png(120, 120), content_type="image/png")
    thumb = gerar_miniatura(relativo, mime="image/png")
    assert thumb is not None and thumb.exists()

    remover(relativo)
    assert not (Path(settings.uploads_dir) / relativo).exists()
    assert not thumb.exists()
