def test_criar_produto_ok(client, vendedora, login):
    cookie = login(vendedora)
    r = client.post(
        "/api/produtos",
        cookies={"texki_session": cookie},
        json={"nome": "DTF por metro", "tipo": "dtf_por_metro"},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["nome"] == "DTF por metro"
    assert body["tipo"] == "dtf_por_metro"


def test_criar_produto_sem_nome(client, vendedora, login):
    cookie = login(vendedora)
    r = client.post(
        "/api/produtos",
        cookies={"texki_session": cookie},
        json={"nome": "", "tipo": "vestuario"},
    )
    assert r.status_code == 422


def test_criar_produto_tipo_invalido(client, vendedora, login):
    cookie = login(vendedora)
    r = client.post(
        "/api/produtos",
        cookies={"texki_session": cookie},
        json={"nome": "X", "tipo": "outro_tipo"},
    )
    assert r.status_code == 422


def test_listar_produtos_inclui_o_recem_criado(client, vendedora, login):
    """Listagem inclui o que acabou de criar. Não assume DB vazio porque o
    seed_catalogo() popula 4 produtos conhecidos."""
    cookie = login(vendedora)
    antes = client.get("/api/produtos", cookies={"texki_session": cookie}).json()
    ids_antes = {p["id"] for p in antes}
    criado = client.post(
        "/api/produtos",
        cookies={"texki_session": cookie},
        json={"nome": "ZZZ_Teste_Listar", "tipo": "vestuario"},
    ).json()
    depois = client.get("/api/produtos", cookies={"texki_session": cookie}).json()
    ids_depois = {p["id"] for p in depois}
    assert criado["id"] in (ids_depois - ids_antes)


def test_listar_produtos_ordenado_por_nome(client, vendedora, login):
    """Verifica a ordem relativa de produtos criados nesta execução (prefixados
    para ficar separados de qualquer seed na baseline)."""
    cookie = login(vendedora)
    pref = "ZZZ_Ord_"
    for nome in [f"{pref}Carlos", f"{pref}Ana", f"{pref}Beatriz"]:
        client.post(
            "/api/produtos",
            cookies={"texki_session": cookie},
            json={"nome": nome, "tipo": "vestuario"},
        )
    r = client.get("/api/produtos", cookies={"texki_session": cookie})
    nomes_test = [p["nome"] for p in r.json() if p["nome"].startswith(pref)]
    assert nomes_test == [f"{pref}Ana", f"{pref}Beatriz", f"{pref}Carlos"]


def test_ver_produto_com_detalhes_vazios(client, vendedora, login):
    cookie = login(vendedora)
    criado = client.post(
        "/api/produtos",
        cookies={"texki_session": cookie},
        json={"nome": "X", "tipo": "vestuario"},
    ).json()
    r = client.get(f"/api/produtos/{criado['id']}", cookies={"texki_session": cookie})
    assert r.status_code == 200
    body = r.json()
    assert body["variacoes"] == []
    assert body["faixas"] == []


def test_ver_produto_inexistente(client, vendedora, login):
    cookie = login(vendedora)
    r = client.get("/api/produtos/99999", cookies={"texki_session": cookie})
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "produto.not_found"


def test_editar_nome_do_produto(client, vendedora, login):
    cookie = login(vendedora)
    criado = client.post(
        "/api/produtos",
        cookies={"texki_session": cookie},
        json={"nome": "Antigo", "tipo": "vestuario"},
    ).json()
    r = client.put(
        f"/api/produtos/{criado['id']}",
        cookies={"texki_session": cookie},
        json={"nome": "Novo"},
    )
    assert r.status_code == 200
    assert r.json()["nome"] == "Novo"


def test_editar_nao_altera_tipo(client, vendedora, login):
    """Schema do PUT só tem `nome`; envio de `tipo` é ignorado, tipo permanece imutável."""
    cookie = login(vendedora)
    criado = client.post(
        "/api/produtos",
        cookies={"texki_session": cookie},
        json={"nome": "X", "tipo": "vestuario"},
    ).json()
    client.put(
        f"/api/produtos/{criado['id']}",
        cookies={"texki_session": cookie},
        json={"nome": "X", "tipo": "dtf_por_metro"},
    )
    detalhe = client.get(
        f"/api/produtos/{criado['id']}", cookies={"texki_session": cookie}
    ).json()
    assert detalhe["tipo"] == "vestuario"


def test_excluir_produto_cascade(client, vendedora, login):
    cookie = login(vendedora)
    criado = client.post(
        "/api/produtos",
        cookies={"texki_session": cookie},
        json={"nome": "X", "tipo": "vestuario"},
    ).json()
    pid = criado["id"]
    client.post(
        f"/api/produtos/{pid}/variacoes",
        cookies={"texki_session": cookie},
        json={"cor": "Preto", "tamanho": "M"},
    )
    client.post(
        f"/api/produtos/{pid}/faixas",
        cookies={"texki_session": cookie},
        json={
            "base": "quantidade",
            "min": "0",
            "max": "10",
            "preco_unitario": "49.90",
        },
    )
    r = client.delete(f"/api/produtos/{pid}", cookies={"texki_session": cookie})
    assert r.status_code == 204

    r = client.get(f"/api/produtos/{pid}", cookies={"texki_session": cookie})
    assert r.status_code == 404


def test_produtos_bloqueia_impressor(client, impressor, login):
    cookie = login(impressor)
    r = client.get("/api/produtos", cookies={"texki_session": cookie})
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "auth.forbidden"


def test_produtos_bloqueia_sem_auth(client):
    r = client.get("/api/produtos")
    assert r.status_code == 401
