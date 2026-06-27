from decimal import Decimal

import pytest


def _criar_produto(client, cookie, nome="X", tipo="dtf_por_metro"):
    return client.post(
        "/api/produtos",
        cookies={"texki_session": cookie},
        json={"nome": nome, "tipo": tipo},
    ).json()


def _criar_faixa(client, cookie, produto_id, base, fmin, fmax, preco):
    return client.post(
        f"/api/produtos/{produto_id}/faixas",
        cookies={"texki_session": cookie},
        json={
            "base": base,
            "min": str(fmin),
            "max": str(fmax) if fmax is not None else None,
            "preco_unitario": str(preco),
        },
    )


# ---------- criação e validação ----------

def test_criar_faixa_dtf_ok(client, vendedora, login):
    cookie = login(vendedora)
    p = _criar_produto(client, cookie)
    r = _criar_faixa(client, cookie, p["id"], "comprimento_m", "0", "5", "69.90")
    assert r.status_code == 201, r.text
    assert Decimal(r.json()["preco_unitario"]) == Decimal("69.90")


def test_criar_faixa_vestuario_ok(client, vendedora, login):
    cookie = login(vendedora)
    p = _criar_produto(client, cookie, nome="Cam", tipo="vestuario")
    r = _criar_faixa(client, cookie, p["id"], "quantidade", "0", "10", "49.90")
    assert r.status_code == 201


def test_base_incompativel_vestuario_pedindo_comprimento(client, vendedora, login):
    cookie = login(vendedora)
    p = _criar_produto(client, cookie, nome="Cam", tipo="vestuario")
    r = _criar_faixa(client, cookie, p["id"], "comprimento_m", "0", "10", "49.90")
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "faixa.base_incompativel"


def test_base_incompativel_dtf_pedindo_quantidade(client, vendedora, login):
    cookie = login(vendedora)
    p = _criar_produto(client, cookie, nome="DTF", tipo="dtf_por_metro")
    r = _criar_faixa(client, cookie, p["id"], "quantidade", "0", "10", "49.90")
    assert r.status_code == 422


def test_min_maior_ou_igual_que_max(client, vendedora, login):
    cookie = login(vendedora)
    p = _criar_produto(client, cookie)
    r = _criar_faixa(client, cookie, p["id"], "comprimento_m", "5", "5", "69.90")
    assert r.status_code == 422
    r2 = _criar_faixa(client, cookie, p["id"], "comprimento_m", "10", "5", "69.90")
    assert r2.status_code == 422


def test_preco_zero_rejeitado(client, vendedora, login):
    cookie = login(vendedora)
    p = _criar_produto(client, cookie)
    r = _criar_faixa(client, cookie, p["id"], "comprimento_m", "0", "5", "0")
    assert r.status_code == 422


def test_faixa_max_nulo_sem_teto(client, vendedora, login):
    cookie = login(vendedora)
    p = _criar_produto(client, cookie)
    r = _criar_faixa(client, cookie, p["id"], "comprimento_m", "20", None, "39.90")
    assert r.status_code == 201
    assert r.json()["max"] is None


# ---------- sobreposição ----------

def test_sobreposicao_rejeitada(client, vendedora, login):
    cookie = login(vendedora)
    p = _criar_produto(client, cookie)
    primeira = _criar_faixa(client, cookie, p["id"], "comprimento_m", "0", "10", "59.90")
    assert primeira.status_code == 201
    segunda = _criar_faixa(client, cookie, p["id"], "comprimento_m", "5", "20", "49.90")
    assert segunda.status_code == 409
    assert segunda.json()["error"]["code"] == "faixa.sobreposicao"


def test_faixas_adjacentes_aceitas(client, vendedora, login):
    """(0,5] e (5,10] tocam na borda mas não se sobrepõem (limite inferior exclusivo)."""
    cookie = login(vendedora)
    p = _criar_produto(client, cookie)
    r1 = _criar_faixa(client, cookie, p["id"], "comprimento_m", "0", "5", "69.90")
    r2 = _criar_faixa(client, cookie, p["id"], "comprimento_m", "5", "10", "59.90")
    assert r1.status_code == 201
    assert r2.status_code == 201


def test_sobreposicao_com_max_nulo(client, vendedora, login):
    """Faixa com max=None (sem teto) sobrepõe qualquer outra que comece antes dela."""
    cookie = login(vendedora)
    p = _criar_produto(client, cookie)
    _criar_faixa(client, cookie, p["id"], "comprimento_m", "20", None, "39.90")
    r = _criar_faixa(client, cookie, p["id"], "comprimento_m", "10", "30", "49.90")
    assert r.status_code == 409


def test_editar_faixa(client, vendedora, login):
    cookie = login(vendedora)
    p = _criar_produto(client, cookie)
    f = _criar_faixa(client, cookie, p["id"], "comprimento_m", "0", "5", "69.90").json()
    r = client.put(
        f"/api/produtos/{p['id']}/faixas/{f['id']}",
        cookies={"texki_session": cookie},
        json={
            "base": "comprimento_m",
            "min": "0",
            "max": "5",
            "preco_unitario": "65.00",
        },
    )
    assert r.status_code == 200
    assert Decimal(r.json()["preco_unitario"]) == Decimal("65.00")


def test_excluir_faixa(client, vendedora, login):
    cookie = login(vendedora)
    p = _criar_produto(client, cookie)
    f = _criar_faixa(client, cookie, p["id"], "comprimento_m", "0", "5", "69.90").json()
    r = client.delete(
        f"/api/produtos/{p['id']}/faixas/{f['id']}",
        cookies={"texki_session": cookie},
    )
    assert r.status_code == 204


# ---------- seleção de faixa — bordas (alma da fatia) ----------

def _setup_dtf_completo(client, cookie):
    p = _criar_produto(client, cookie, nome="DTF", tipo="dtf_por_metro")
    _criar_faixa(client, cookie, p["id"], "comprimento_m", "0", "5", "69.90")
    _criar_faixa(client, cookie, p["id"], "comprimento_m", "5", "10", "59.90")
    _criar_faixa(client, cookie, p["id"], "comprimento_m", "10", "20", "49.90")
    _criar_faixa(client, cookie, p["id"], "comprimento_m", "20", None, "39.90")
    return p["id"]


def _setup_camiseta_completo(client, cookie):
    p = _criar_produto(client, cookie, nome="Cam", tipo="vestuario")
    _criar_faixa(client, cookie, p["id"], "quantidade", "0", "10", "49.90")
    _criar_faixa(client, cookie, p["id"], "quantidade", "10", "50", "39.90")
    _criar_faixa(client, cookie, p["id"], "quantidade", "50", None, "29.90")
    return p["id"]


@pytest.mark.parametrize(
    "medida,esperado",
    [
        ("0.01", "69.90"),
        ("5.00", "69.90"),
        ("5.01", "59.90"),
        ("10.00", "59.90"),
        ("10.01", "49.90"),
        ("20.00", "49.90"),
        ("20.01", "39.90"),
        ("100.00", "39.90"),
    ],
)
def test_selecao_dtf_bordas(client, vendedora, login, medida, esperado):
    cookie = login(vendedora)
    pid = _setup_dtf_completo(client, cookie)
    r = client.get(
        f"/api/produtos/{pid}/preco",
        cookies={"texki_session": cookie},
        params={"medida": medida},
    )
    assert r.status_code == 200, r.text
    assert Decimal(r.json()["preco_unitario"]) == Decimal(esperado)


@pytest.mark.parametrize(
    "medida,esperado",
    [
        ("1", "49.90"),
        ("10", "49.90"),
        ("11", "39.90"),
        ("50", "39.90"),
        ("51", "29.90"),
        ("500", "29.90"),
    ],
)
def test_selecao_camiseta_bordas(client, vendedora, login, medida, esperado):
    cookie = login(vendedora)
    pid = _setup_camiseta_completo(client, cookie)
    r = client.get(
        f"/api/produtos/{pid}/preco",
        cookies={"texki_session": cookie},
        params={"medida": medida},
    )
    assert r.status_code == 200, r.text
    assert Decimal(r.json()["preco_unitario"]) == Decimal(esperado)


def test_selecao_medida_sem_faixa_correspondente(client, vendedora, login):
    """Configuração com lacuna: medida 1 não cai em nenhuma faixa."""
    cookie = login(vendedora)
    p = _criar_produto(client, cookie, nome="Inc", tipo="dtf_por_metro")
    _criar_faixa(client, cookie, p["id"], "comprimento_m", "5", "10", "59.90")
    r = client.get(
        f"/api/produtos/{p['id']}/preco",
        cookies={"texki_session": cookie},
        params={"medida": "1.00"},
    )
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "preco.sem_faixa_para_medida"


def test_selecao_medida_zero_invalida(client, vendedora, login):
    cookie = login(vendedora)
    p = _criar_produto(client, cookie)
    r = client.get(
        f"/api/produtos/{p['id']}/preco",
        cookies={"texki_session": cookie},
        params={"medida": "0"},
    )
    assert r.status_code == 422


def test_selecao_produto_inexistente(client, vendedora, login):
    cookie = login(vendedora)
    r = client.get(
        "/api/produtos/99999/preco",
        cookies={"texki_session": cookie},
        params={"medida": "5"},
    )
    assert r.status_code == 404


def test_faixas_bloqueia_impressor(client, vendedora, impressor, login):
    cookie_v = login(vendedora)
    p = _criar_produto(client, cookie_v)
    cookie_i = login(impressor)
    r = client.post(
        f"/api/produtos/{p['id']}/faixas",
        cookies={"texki_session": cookie_i},
        json={
            "base": "comprimento_m",
            "min": "0",
            "max": "5",
            "preco_unitario": "69.90",
        },
    )
    assert r.status_code == 403
