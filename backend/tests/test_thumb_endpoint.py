"""Endpoint da miniatura (Fatia 4 — RNF4)."""
import io
from datetime import date, timedelta
from pathlib import Path

from PIL import Image

from app.core.config import settings


TELEFONE = "(11) 90000-0003"


def _png(largura, altura) -> bytes:
    img = Image.new("RGBA", (largura, altura), (0, 200, 0, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _pdf() -> bytes:
    return b"%PDF-1.4\n%mini\n"


def _criar_cli_prod_pedido(client, cookie):
    cli = client.post(
        "/api/clientes",
        cookies={"texki_session": cookie},
        json={
            "primeiro_nome": "Thu",
            "telefone": TELEFONE,
            "consentimento_lgpd": False,
        },
    ).json()
    p = client.post(
        "/api/produtos",
        cookies={"texki_session": cookie},
        json={"nome": "ZZZ_Thumb_Prod", "tipo": "vestuario"},
    ).json()
    client.post(
        f"/api/produtos/{p['id']}/faixas",
        cookies={"texki_session": cookie},
        json={
            "base": "quantidade",
            "min": "0",
            "max": "10",
            "preco_unitario": "10.00",
        },
    )
    v = client.post(
        f"/api/produtos/{p['id']}/variacoes",
        cookies={"texki_session": cookie},
        json={"cor": "Vermelho", "tamanho": "M"},
    ).json()
    pedido = client.post(
        "/api/pedidos",
        cookies={"texki_session": cookie},
        json={
            "cliente_id": cli["id"],
            "data_entrega": (date.today() + timedelta(days=1)).isoformat(),
            "itens": [
                {"produto_id": p["id"], "variacao_id": v["id"], "quantidade": "1"}
            ],
        },
    ).json()
    return pedido


def test_thumb_png_serve_e_cacheia(client, vendedora, login):
    cookie = login(vendedora)
    pedido = _criar_cli_prod_pedido(client, cookie)
    arte = client.post(
        f"/api/pedidos/{pedido['id']}/artes",
        cookies={"texki_session": cookie},
        files={"arquivo": ("a.png", _png(800, 400), "image/png")},
        # proporção 2 → 30×15 cm
        data={"largura_cm": "30", "altura_cm": "15"},
    ).json()

    r1 = client.get(
        f"/api/pedidos/{pedido['id']}/artes/{arte['id']}/thumb",
        cookies={"texki_session": cookie},
    )
    assert r1.status_code == 200, r1.text
    assert r1.headers["content-type"] == "image/png"

    # Lê tamanho do PNG retornado para garantir que foi redimensionado.
    with Image.open(io.BytesIO(r1.content)) as t:
        w, h = t.size
    assert max(w, h) <= 256
    assert w == 256 and h == 128  # 2:1 reduzido

    # Segunda chamada usa o thumb já em disco (não regenera).
    arquivos_thumb = list(Path(settings.uploads_dir).glob("*_thumb.png"))
    assert len(arquivos_thumb) == 1
    mtime = arquivos_thumb[0].stat().st_mtime

    r2 = client.get(
        f"/api/pedidos/{pedido['id']}/artes/{arte['id']}/thumb",
        cookies={"texki_session": cookie},
    )
    assert r2.status_code == 200
    assert arquivos_thumb[0].stat().st_mtime == mtime


def test_thumb_pdf_devolve_404(client, vendedora, login):
    cookie = login(vendedora)
    pedido = _criar_cli_prod_pedido(client, cookie)
    arte = client.post(
        f"/api/pedidos/{pedido['id']}/artes",
        cookies={"texki_session": cookie},
        files={"arquivo": ("a.pdf", _pdf(), "application/pdf")},
        data={"largura_cm": "30", "altura_cm": "20"},
    ).json()

    r = client.get(
        f"/api/pedidos/{pedido['id']}/artes/{arte['id']}/thumb",
        cookies={"texki_session": cookie},
    )
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "arte.sem_miniatura"


def test_thumb_impressor_pode_baixar(
    client, vendedora, impressor, login
):
    cookie_v = login(vendedora)
    pedido = _criar_cli_prod_pedido(client, cookie_v)
    arte = client.post(
        f"/api/pedidos/{pedido['id']}/artes",
        cookies={"texki_session": cookie_v},
        files={"arquivo": ("a.png", _png(200, 100), "image/png")},
        data={"largura_cm": "30", "altura_cm": "15"},
    ).json()

    cookie_i = login(impressor)
    r = client.get(
        f"/api/pedidos/{pedido['id']}/artes/{arte['id']}/thumb",
        cookies={"texki_session": cookie_i},
    )
    assert r.status_code == 200
