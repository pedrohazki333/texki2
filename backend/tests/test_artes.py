"""Testes do upload de artes (RNF1) e da regra de proporção via API."""
import io
from datetime import date, timedelta
from pathlib import Path

import pytest
from PIL import Image
from sqlalchemy import select

from app.core.config import settings
from app.models.arte import Arte

TELEFONE = "(11) 98765-4321"


def _png_bytes(largura_px: int, altura_px: int, padding: int = 0) -> bytes:
    canvas_w = largura_px + padding * 2
    canvas_h = altura_px + padding * 2
    img = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    for x in range(padding, padding + largura_px):
        for y in range(padding, padding + altura_px):
            img.putpixel((x, y), (255, 0, 0, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _pdf_bytes() -> bytes:
    # PDF mínimo válido o suficiente para passar pelo content-type check.
    # Não precisa ser parseável — só o storage olha o mime.
    return b"%PDF-1.4\n%fake\n"


def _criar_cliente(client, cookie) -> dict:
    return client.post(
        "/api/clientes",
        cookies={"texki_session": cookie},
        json={"primeiro_nome": "Cli", "telefone": TELEFONE, "consentimento_lgpd": False},
    ).json()


def _criar_produto_e_variacao(client, cookie) -> tuple[dict, dict]:
    p = client.post(
        "/api/produtos",
        cookies={"texki_session": cookie},
        json={"nome": "ZZZ_Art_Cam", "tipo": "vestuario"},
    ).json()
    client.post(
        f"/api/produtos/{p['id']}/faixas",
        cookies={"texki_session": cookie},
        json={"base": "quantidade", "min": "0", "max": "10", "preco_unitario": "49.90"},
    )
    v = client.post(
        f"/api/produtos/{p['id']}/variacoes",
        cookies={"texki_session": cookie},
        json={"cor": "Preto", "tamanho": "M"},
    ).json()
    return p, v


def _criar_pedido(client, cookie) -> dict:
    cli = _criar_cliente(client, cookie)
    p, v = _criar_produto_e_variacao(client, cookie)
    return client.post(
        "/api/pedidos",
        cookies={"texki_session": cookie},
        json={
            "cliente_id": cli["id"],
            "data_entrega": (date.today() + timedelta(days=2)).isoformat(),
            "itens": [
                {"produto_id": p["id"], "variacao_id": v["id"], "quantidade": "1"}
            ],
        },
    ).json()


# ---------- analisar (sem persistir) ----------

def test_analisar_png_devolve_proporcao(client, vendedora, login):
    cookie = login(vendedora)
    pedido = _criar_pedido(client, cookie)
    r = client.post(
        f"/api/pedidos/{pedido['id']}/artes/analisar",
        cookies={"texki_session": cookie},
        files={"arquivo": ("a.png", _png_bytes(200, 100), "image/png")},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["mime"] == "image/png"
    assert body["cadeado"] == "fechado"
    assert float(body["proporcao"]) == pytest.approx(2.0)


def test_analisar_pdf_nao_calcula_proporcao(client, vendedora, login):
    cookie = login(vendedora)
    pedido = _criar_pedido(client, cookie)
    r = client.post(
        f"/api/pedidos/{pedido['id']}/artes/analisar",
        cookies={"texki_session": cookie},
        files={"arquivo": ("a.pdf", _pdf_bytes(), "application/pdf")},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["proporcao"] is None
    assert body["cadeado"] == "aberto"


# ---------- criação ----------

def test_criar_arte_png_valida_e_persiste(client, vendedora, login):
    cookie = login(vendedora)
    pedido = _criar_pedido(client, cookie)
    dados = _png_bytes(200, 100)
    r = client.post(
        f"/api/pedidos/{pedido['id']}/artes",
        cookies={"texki_session": cookie},
        files={"arquivo": ("a.png", dados, "image/png")},
        # proporção 2 → 30×15 cm bate.
        data={"largura_cm": "30", "altura_cm": "15", "observacoes": "frente"},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["ordem"] == 1
    assert body["observacoes"] == "frente"
    # arquivo deve existir no diretório de uploads
    arquivos = list(Path(settings.uploads_dir).iterdir())
    assert len(arquivos) == 1


def test_criar_arte_png_com_proporcao_divergente_eh_rejeitada(
    client, vendedora, login
):
    cookie = login(vendedora)
    pedido = _criar_pedido(client, cookie)
    r = client.post(
        f"/api/pedidos/{pedido['id']}/artes",
        cookies={"texki_session": cookie},
        files={"arquivo": ("a.png", _png_bytes(200, 100), "image/png")},
        # proporção 2 mas usuário forçou 30×20 → divergente.
        data={"largura_cm": "30", "altura_cm": "20"},
    )
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "arte.proporcao_divergente"


def test_criar_arte_pdf_aceita_medidas_quaisquer(client, vendedora, login):
    cookie = login(vendedora)
    pedido = _criar_pedido(client, cookie)
    r = client.post(
        f"/api/pedidos/{pedido['id']}/artes",
        cookies={"texki_session": cookie},
        files={"arquivo": ("a.pdf", _pdf_bytes(), "application/pdf")},
        data={"largura_cm": "30", "altura_cm": "20"},  # qualquer valor
    )
    assert r.status_code == 201, r.text


def test_formato_invalido_eh_barrado(client, vendedora, login):
    cookie = login(vendedora)
    pedido = _criar_pedido(client, cookie)
    r = client.post(
        f"/api/pedidos/{pedido['id']}/artes",
        cookies={"texki_session": cookie},
        files={"arquivo": ("a.jpg", b"fake-jpg", "image/jpeg")},
        data={"largura_cm": "30", "altura_cm": "15"},
    )
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "arte.formato_invalido"


def test_tamanho_acima_de_25mb_eh_barrado(client, vendedora, login):
    cookie = login(vendedora)
    pedido = _criar_pedido(client, cookie)
    # 25 MB + 1 byte de PDF "minimal".
    gordo = b"%PDF-1.4\n" + b"x" * (25 * 1024 * 1024)
    r = client.post(
        f"/api/pedidos/{pedido['id']}/artes",
        cookies={"texki_session": cookie},
        files={"arquivo": ("a.pdf", gordo, "application/pdf")},
        data={"largura_cm": "30", "altura_cm": "15"},
    )
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "arte.tamanho_excedido"


def test_ordem_incrementa_a_cada_arte(client, vendedora, login):
    cookie = login(vendedora)
    pedido = _criar_pedido(client, cookie)
    dados = _png_bytes(200, 100)
    ordens = []
    for _ in range(3):
        r = client.post(
            f"/api/pedidos/{pedido['id']}/artes",
            cookies={"texki_session": cookie},
            files={"arquivo": ("a.png", dados, "image/png")},
            data={"largura_cm": "30", "altura_cm": "15"},
        )
        assert r.status_code == 201
        ordens.append(r.json()["ordem"])
    assert ordens == [1, 2, 3]


def test_arte_aparece_no_detalhes_do_pedido(client, vendedora, login):
    cookie = login(vendedora)
    pedido = _criar_pedido(client, cookie)
    client.post(
        f"/api/pedidos/{pedido['id']}/artes",
        cookies={"texki_session": cookie},
        files={"arquivo": ("a.png", _png_bytes(200, 100), "image/png")},
        data={"largura_cm": "30", "altura_cm": "15"},
    )
    r = client.get(f"/api/pedidos/{pedido['id']}", cookies={"texki_session": cookie})
    assert r.status_code == 200
    assert len(r.json()["artes"]) == 1


# ---------- exclusão ----------

def test_excluir_arte_remove_registro_e_arquivo(
    client, vendedora, login, db_session
):
    cookie = login(vendedora)
    pedido = _criar_pedido(client, cookie)
    criada = client.post(
        f"/api/pedidos/{pedido['id']}/artes",
        cookies={"texki_session": cookie},
        files={"arquivo": ("a.png", _png_bytes(200, 100), "image/png")},
        data={"largura_cm": "30", "altura_cm": "15"},
    ).json()
    arte_db = db_session.scalar(select(Arte).where(Arte.id == criada["id"]))
    caminho = Path(settings.uploads_dir) / arte_db.arquivo_path
    assert caminho.exists()

    r = client.delete(
        f"/api/pedidos/{pedido['id']}/artes/{criada['id']}",
        cookies={"texki_session": cookie},
    )
    assert r.status_code == 204
    assert not caminho.exists()


# ---------- RBAC ----------

def test_artes_bloqueia_impressor_para_criar(client, impressor, login):
    cookie = login(impressor)
    # nem precisa criar pedido — RBAC barra antes.
    r = client.post(
        "/api/pedidos/1/artes/analisar",
        cookies={"texki_session": cookie},
        files={"arquivo": ("a.png", _png_bytes(10, 10), "image/png")},
    )
    assert r.status_code == 403


def test_artes_bloqueia_sem_auth(client):
    r = client.post(
        "/api/pedidos/1/artes/analisar",
        files={"arquivo": ("a.png", _png_bytes(10, 10), "image/png")},
    )
    assert r.status_code == 401
