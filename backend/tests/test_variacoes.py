def _criar_produto(client, cookie, nome="X", tipo="vestuario"):
    return client.post(
        "/api/produtos",
        cookies={"texki_session": cookie},
        json={"nome": nome, "tipo": tipo},
    ).json()


def test_criar_variacao_em_vestuario(client, vendedora, login):
    cookie = login(vendedora)
    p = _criar_produto(client, cookie)
    r = client.post(
        f"/api/produtos/{p['id']}/variacoes",
        cookies={"texki_session": cookie},
        json={"cor": "Preto", "tamanho": "M"},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["cor"] == "Preto"
    assert body["tamanho"] == "M"


def test_criar_variacao_em_dtf_bloqueado(client, vendedora, login):
    cookie = login(vendedora)
    p = _criar_produto(client, cookie, nome="DTF", tipo="dtf_por_metro")
    r = client.post(
        f"/api/produtos/{p['id']}/variacoes",
        cookies={"texki_session": cookie},
        json={"cor": "X", "tamanho": "Y"},
    )
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "variacao.tipo_invalido"


def test_variacao_duplicada_bloqueada(client, vendedora, login):
    cookie = login(vendedora)
    p = _criar_produto(client, cookie)
    primeira = client.post(
        f"/api/produtos/{p['id']}/variacoes",
        cookies={"texki_session": cookie},
        json={"cor": "Preto", "tamanho": "M"},
    )
    assert primeira.status_code == 201
    segunda = client.post(
        f"/api/produtos/{p['id']}/variacoes",
        cookies={"texki_session": cookie},
        json={"cor": "Preto", "tamanho": "M"},
    )
    assert segunda.status_code == 409
    assert segunda.json()["error"]["code"] == "variacao.duplicada"


def test_variacao_mesma_cor_tamanho_em_produtos_diferentes_ok(client, vendedora, login):
    cookie = login(vendedora)
    a = _criar_produto(client, cookie, nome="A")
    b = _criar_produto(client, cookie, nome="B")
    r1 = client.post(
        f"/api/produtos/{a['id']}/variacoes",
        cookies={"texki_session": cookie},
        json={"cor": "Preto", "tamanho": "M"},
    )
    r2 = client.post(
        f"/api/produtos/{b['id']}/variacoes",
        cookies={"texki_session": cookie},
        json={"cor": "Preto", "tamanho": "M"},
    )
    assert r1.status_code == 201
    assert r2.status_code == 201


def test_editar_variacao(client, vendedora, login):
    cookie = login(vendedora)
    p = _criar_produto(client, cookie)
    v = client.post(
        f"/api/produtos/{p['id']}/variacoes",
        cookies={"texki_session": cookie},
        json={"cor": "Preto", "tamanho": "M"},
    ).json()
    r = client.put(
        f"/api/produtos/{p['id']}/variacoes/{v['id']}",
        cookies={"texki_session": cookie},
        json={"cor": "Branco", "tamanho": "G"},
    )
    assert r.status_code == 200
    assert r.json()["cor"] == "Branco"
    assert r.json()["tamanho"] == "G"


def test_excluir_variacao(client, vendedora, login):
    cookie = login(vendedora)
    p = _criar_produto(client, cookie)
    v = client.post(
        f"/api/produtos/{p['id']}/variacoes",
        cookies={"texki_session": cookie},
        json={"cor": "Preto", "tamanho": "M"},
    ).json()
    r = client.delete(
        f"/api/produtos/{p['id']}/variacoes/{v['id']}",
        cookies={"texki_session": cookie},
    )
    assert r.status_code == 204
    detalhe = client.get(
        f"/api/produtos/{p['id']}", cookies={"texki_session": cookie}
    ).json()
    assert detalhe["variacoes"] == []


def test_variacao_inexistente_404(client, vendedora, login):
    cookie = login(vendedora)
    p = _criar_produto(client, cookie)
    r = client.delete(
        f"/api/produtos/{p['id']}/variacoes/99999",
        cookies={"texki_session": cookie},
    )
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "variacao.not_found"
