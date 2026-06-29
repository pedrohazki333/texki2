from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.models.auditoria import Auditoria
from app.models.faixa_preco import FaixaPreco

TELEFONE = "(11) 98765-4321"


# ---------- helpers ----------

def _criar_cliente(client, cookie, nome="Cli", telefone=TELEFONE) -> dict:
    r = client.post(
        "/api/clientes",
        cookies={"texki_session": cookie},
        json={"primeiro_nome": nome, "telefone": telefone, "consentimento_lgpd": False},
    )
    assert r.status_code == 201, r.text
    return r.json()


def _criar_produto(client, cookie, nome, tipo) -> dict:
    r = client.post(
        "/api/produtos",
        cookies={"texki_session": cookie},
        json={"nome": nome, "tipo": tipo},
    )
    assert r.status_code == 201, r.text
    return r.json()


def _criar_faixa(client, cookie, pid, base, fmin, fmax, preco) -> dict:
    r = client.post(
        f"/api/produtos/{pid}/faixas",
        cookies={"texki_session": cookie},
        json={
            "base": base,
            "min": str(fmin),
            "max": str(fmax) if fmax is not None else None,
            "preco_unitario": str(preco),
        },
    )
    assert r.status_code == 201, r.text
    return r.json()


def _criar_variacao(client, cookie, pid, cor="Preto", tamanho="M") -> dict:
    r = client.post(
        f"/api/produtos/{pid}/variacoes",
        cookies={"texki_session": cookie},
        json={"cor": cor, "tamanho": tamanho},
    )
    assert r.status_code == 201, r.text
    return r.json()


def _camiseta_pronta(client, cookie) -> tuple[dict, dict]:
    p = _criar_produto(client, cookie, nome="ZZZ_Camiseta", tipo="vestuario")
    _criar_faixa(client, cookie, p["id"], "quantidade", "0", "10", "49.90")
    _criar_faixa(client, cookie, p["id"], "quantidade", "10", "50", "39.90")
    _criar_faixa(client, cookie, p["id"], "quantidade", "50", None, "29.90")
    v = _criar_variacao(client, cookie, p["id"])
    return p, v


def _dtf_pronto(client, cookie) -> dict:
    p = _criar_produto(client, cookie, nome="ZZZ_DTF", tipo="dtf_por_metro")
    _criar_faixa(client, cookie, p["id"], "comprimento_m", "0", "5", "69.90")
    _criar_faixa(client, cookie, p["id"], "comprimento_m", "5", "10", "59.90")
    _criar_faixa(client, cookie, p["id"], "comprimento_m", "10", "20", "49.90")
    _criar_faixa(client, cookie, p["id"], "comprimento_m", "20", None, "39.90")
    return p


def _amanha() -> str:
    return (date.today() + timedelta(days=1)).isoformat()


# ---------- criação ----------

def test_criar_pedido_minimo_com_um_item(client, vendedora, login):
    cookie = login(vendedora)
    cli = _criar_cliente(client, cookie)
    p, v = _camiseta_pronta(client, cookie)

    r = client.post(
        "/api/pedidos",
        cookies={"texki_session": cookie},
        json={
            "cliente_id": cli["id"],
            "data_entrega": _amanha(),
            "itens": [
                {"produto_id": p["id"], "variacao_id": v["id"], "quantidade": "15"}
            ],
        },
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["status"] == "recebido"
    assert body["cliente_id"] == cli["id"]
    assert body["vendedora_id"] == vendedora.id
    # 15 camisetas → faixa (10, 50] → 39.90/un
    assert Decimal(body["itens"][0]["preco_unitario"]) == Decimal("39.90")
    assert Decimal(body["itens"][0]["subtotal"]) == Decimal("598.50")
    assert Decimal(body["total"]) == Decimal("598.50")


def test_criar_pedido_dtf_por_metro_calcula_pela_faixa(client, vendedora, login):
    cookie = login(vendedora)
    cli = _criar_cliente(client, cookie)
    p = _dtf_pronto(client, cookie)

    r = client.post(
        "/api/pedidos",
        cookies={"texki_session": cookie},
        json={
            "cliente_id": cli["id"],
            "data_entrega": _amanha(),
            # 7 metros → faixa (5, 10] → 59.90/m → subtotal 419.30
            "itens": [{"produto_id": p["id"], "quantidade": "7"}],
        },
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert Decimal(body["itens"][0]["preco_unitario"]) == Decimal("59.90")
    assert Decimal(body["total"]) == Decimal("419.30")


def test_criar_pedido_soma_total_de_varios_itens(client, vendedora, login):
    cookie = login(vendedora)
    cli = _criar_cliente(client, cookie)
    cam, v = _camiseta_pronta(client, cookie)
    dtf = _dtf_pronto(client, cookie)

    r = client.post(
        "/api/pedidos",
        cookies={"texki_session": cookie},
        json={
            "cliente_id": cli["id"],
            "data_entrega": _amanha(),
            "itens": [
                # 2 camisetas → (0,10] → 49.90 → 99.80
                {"produto_id": cam["id"], "variacao_id": v["id"], "quantidade": "2"},
                # 12 metros DTF → (10,20] → 49.90 → 598.80
                {"produto_id": dtf["id"], "quantidade": "12"},
            ],
        },
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert Decimal(body["total"]) == Decimal("698.60")


def test_criar_pedido_sem_itens_eh_rejeitado(client, vendedora, login):
    cookie = login(vendedora)
    cli = _criar_cliente(client, cookie)
    r = client.post(
        "/api/pedidos",
        cookies={"texki_session": cookie},
        json={"cliente_id": cli["id"], "data_entrega": _amanha(), "itens": []},
    )
    assert r.status_code == 422


def test_criar_pedido_quantidade_zero_eh_rejeitada(client, vendedora, login):
    cookie = login(vendedora)
    cli = _criar_cliente(client, cookie)
    p, v = _camiseta_pronta(client, cookie)
    r = client.post(
        "/api/pedidos",
        cookies={"texki_session": cookie},
        json={
            "cliente_id": cli["id"],
            "data_entrega": _amanha(),
            "itens": [
                {"produto_id": p["id"], "variacao_id": v["id"], "quantidade": "0"}
            ],
        },
    )
    assert r.status_code == 422


def test_criar_pedido_vestuario_sem_variacao_eh_rejeitado(client, vendedora, login):
    cookie = login(vendedora)
    cli = _criar_cliente(client, cookie)
    p, _v = _camiseta_pronta(client, cookie)
    r = client.post(
        "/api/pedidos",
        cookies={"texki_session": cookie},
        json={
            "cliente_id": cli["id"],
            "data_entrega": _amanha(),
            "itens": [{"produto_id": p["id"], "quantidade": "5"}],
        },
    )
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "pedido.variacao_obrigatoria"


def test_criar_pedido_dtf_com_variacao_eh_rejeitado(client, vendedora, login):
    cookie = login(vendedora)
    cli = _criar_cliente(client, cookie)
    cam, v = _camiseta_pronta(client, cookie)
    dtf = _dtf_pronto(client, cookie)
    r = client.post(
        "/api/pedidos",
        cookies={"texki_session": cookie},
        json={
            "cliente_id": cli["id"],
            "data_entrega": _amanha(),
            # variação não pertence ao DTF (e DTF não aceita variação)
            "itens": [
                {"produto_id": dtf["id"], "variacao_id": v["id"], "quantidade": "5"}
            ],
        },
    )
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "pedido.variacao_indevida"


def test_criar_pedido_variacao_de_outro_produto_eh_rejeitada(client, vendedora, login):
    cookie = login(vendedora)
    cli = _criar_cliente(client, cookie)
    p1, v1 = _camiseta_pronta(client, cookie)
    p2 = _criar_produto(client, cookie, nome="ZZZ_Cam2", tipo="vestuario")
    _criar_faixa(client, cookie, p2["id"], "quantidade", "0", "10", "30.00")
    # tenta usar variação de p1 dentro do item do p2
    r = client.post(
        "/api/pedidos",
        cookies={"texki_session": cookie},
        json={
            "cliente_id": cli["id"],
            "data_entrega": _amanha(),
            "itens": [
                {"produto_id": p2["id"], "variacao_id": v1["id"], "quantidade": "3"}
            ],
        },
    )
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "pedido.variacao_invalida"


def test_criar_pedido_cliente_inexistente(client, vendedora, login):
    cookie = login(vendedora)
    p, v = _camiseta_pronta(client, cookie)
    r = client.post(
        "/api/pedidos",
        cookies={"texki_session": cookie},
        json={
            "cliente_id": 999999,
            "data_entrega": _amanha(),
            "itens": [
                {"produto_id": p["id"], "variacao_id": v["id"], "quantidade": "1"}
            ],
        },
    )
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "pedido.cliente_inexistente"


# ---------- congelamento ----------

def test_preco_congelado_resiste_a_mudanca_de_faixa(
    client, vendedora, login, db_session
):
    """Mudar a faixa depois de criado NÃO altera preco_unitario/subtotal do pedido."""
    cookie = login(vendedora)
    cli = _criar_cliente(client, cookie)
    p, v = _camiseta_pronta(client, cookie)
    # 15 camisetas → 39.90/un → 598.50
    criado = client.post(
        "/api/pedidos",
        cookies={"texki_session": cookie},
        json={
            "cliente_id": cli["id"],
            "data_entrega": _amanha(),
            "itens": [
                {"produto_id": p["id"], "variacao_id": v["id"], "quantidade": "15"}
            ],
        },
    ).json()

    # muda a faixa (10,50] para 19.90 — direto no banco
    faixa = db_session.scalar(
        select(FaixaPreco).where(
            FaixaPreco.produto_id == p["id"],
            FaixaPreco.min == Decimal("10"),
        )
    )
    assert faixa is not None
    faixa.preco_unitario = Decimal("19.90")
    db_session.commit()

    # ao reler o pedido, preço/subtotal/total devem ser os originais
    r = client.get(f"/api/pedidos/{criado['id']}", cookies={"texki_session": cookie})
    assert r.status_code == 200
    body = r.json()
    assert Decimal(body["itens"][0]["preco_unitario"]) == Decimal("39.90")
    assert Decimal(body["itens"][0]["subtotal"]) == Decimal("598.50")
    assert Decimal(body["total"]) == Decimal("598.50")


def test_editar_quantidade_recalcula_preco_pela_faixa_atual(
    client, vendedora, login
):
    """Editar o item recalcula o preço pela faixa correspondente à nova quantidade
    e re-congela. Mudar de 5 (faixa 0,10] → 49.90) para 15 (faixa (10,50] → 39.90)."""
    cookie = login(vendedora)
    cli = _criar_cliente(client, cookie)
    p, v = _camiseta_pronta(client, cookie)
    criado = client.post(
        "/api/pedidos",
        cookies={"texki_session": cookie},
        json={
            "cliente_id": cli["id"],
            "data_entrega": _amanha(),
            "itens": [
                {"produto_id": p["id"], "variacao_id": v["id"], "quantidade": "5"}
            ],
        },
    ).json()
    assert Decimal(criado["itens"][0]["preco_unitario"]) == Decimal("49.90")

    r = client.put(
        f"/api/pedidos/{criado['id']}",
        cookies={"texki_session": cookie},
        json={
            "cliente_id": cli["id"],
            "data_entrega": _amanha(),
            "itens": [
                {"produto_id": p["id"], "variacao_id": v["id"], "quantidade": "15"}
            ],
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert Decimal(body["itens"][0]["preco_unitario"]) == Decimal("39.90")
    assert Decimal(body["total"]) == Decimal("598.50")


# ---------- listagem / leitura ----------

def test_obter_pedido_inexistente(client, vendedora, login):
    cookie = login(vendedora)
    r = client.get("/api/pedidos/999999", cookies={"texki_session": cookie})
    assert r.status_code == 404


# ---------- exclusão ----------

def test_excluir_pedido(client, vendedora, login):
    cookie = login(vendedora)
    cli = _criar_cliente(client, cookie)
    p, v = _camiseta_pronta(client, cookie)
    criado = client.post(
        "/api/pedidos",
        cookies={"texki_session": cookie},
        json={
            "cliente_id": cli["id"],
            "data_entrega": _amanha(),
            "itens": [
                {"produto_id": p["id"], "variacao_id": v["id"], "quantidade": "2"}
            ],
        },
    ).json()
    r = client.delete(
        f"/api/pedidos/{criado['id']}", cookies={"texki_session": cookie}
    )
    assert r.status_code == 204


# ---------- bloqueios de exclusão herdados (LGPD / produto) ----------

def test_cliente_com_pedidos_nao_pode_ser_excluido(client, vendedora, login):
    cookie = login(vendedora)
    cli = _criar_cliente(client, cookie)
    p, v = _camiseta_pronta(client, cookie)
    client.post(
        "/api/pedidos",
        cookies={"texki_session": cookie},
        json={
            "cliente_id": cli["id"],
            "data_entrega": _amanha(),
            "itens": [
                {"produto_id": p["id"], "variacao_id": v["id"], "quantidade": "1"}
            ],
        },
    )
    r = client.delete(f"/api/clientes/{cli['id']}", cookies={"texki_session": cookie})
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "cliente.tem_pedidos"


def test_anonimizar_cliente_com_pedidos(client, vendedora, login):
    cookie = login(vendedora)
    cli = _criar_cliente(client, cookie, nome="Maria")
    p, v = _camiseta_pronta(client, cookie)
    client.post(
        "/api/pedidos",
        cookies={"texki_session": cookie},
        json={
            "cliente_id": cli["id"],
            "data_entrega": _amanha(),
            "itens": [
                {"produto_id": p["id"], "variacao_id": v["id"], "quantidade": "1"}
            ],
        },
    )
    r = client.post(
        f"/api/clientes/{cli['id']}/anonimizar", cookies={"texki_session": cookie}
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["primeiro_nome"] == "(cliente anonimizado)"
    assert body["telefone"] == "(removido)"
    assert body["endereco"] is None


def test_produto_com_itens_nao_pode_ser_excluido(client, vendedora, login):
    cookie = login(vendedora)
    cli = _criar_cliente(client, cookie)
    p, v = _camiseta_pronta(client, cookie)
    client.post(
        "/api/pedidos",
        cookies={"texki_session": cookie},
        json={
            "cliente_id": cli["id"],
            "data_entrega": _amanha(),
            "itens": [
                {"produto_id": p["id"], "variacao_id": v["id"], "quantidade": "1"}
            ],
        },
    )
    r = client.delete(f"/api/produtos/{p['id']}", cookies={"texki_session": cookie})
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "produto.tem_itens"


# ---------- responsável (RBAC + auditoria) ----------

def test_vendedora_nao_pode_trocar_responsavel(
    client, vendedora, admin, login
):
    cookie_v = login(vendedora)
    cli = _criar_cliente(client, cookie_v)
    p, v = _camiseta_pronta(client, cookie_v)
    criado = client.post(
        "/api/pedidos",
        cookies={"texki_session": cookie_v},
        json={
            "cliente_id": cli["id"],
            "data_entrega": _amanha(),
            "itens": [
                {"produto_id": p["id"], "variacao_id": v["id"], "quantidade": "1"}
            ],
        },
    ).json()
    r = client.put(
        f"/api/pedidos/{criado['id']}/responsavel",
        cookies={"texki_session": cookie_v},
        json={"vendedora_id": admin.id},
    )
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "auth.forbidden"


def test_admin_troca_responsavel_e_audita(
    client, vendedora, admin, login, db_session
):
    cookie_v = login(vendedora)
    cli = _criar_cliente(client, cookie_v)
    p, v = _camiseta_pronta(client, cookie_v)
    criado = client.post(
        "/api/pedidos",
        cookies={"texki_session": cookie_v},
        json={
            "cliente_id": cli["id"],
            "data_entrega": _amanha(),
            "itens": [
                {"produto_id": p["id"], "variacao_id": v["id"], "quantidade": "1"}
            ],
        },
    ).json()
    cookie_adm = login(admin)
    r = client.put(
        f"/api/pedidos/{criado['id']}/responsavel",
        cookies={"texki_session": cookie_adm},
        json={"vendedora_id": admin.id},
    )
    assert r.status_code == 200, r.text
    assert r.json()["vendedora_id"] == admin.id

    linhas = db_session.scalars(
        select(Auditoria).where(
            Auditoria.entidade == "pedido",
            Auditoria.entidade_id == criado["id"],
            Auditoria.campo == "vendedora_id",
        )
    ).all()
    assert len(linhas) == 1
    assert linhas[0].usuario_id == admin.id
    assert linhas[0].valor_anterior == str(vendedora.id)
    assert linhas[0].valor_novo == str(admin.id)


def test_admin_trocar_responsavel_para_impressor_rejeita(
    client, vendedora, admin, impressor, login
):
    cookie_v = login(vendedora)
    cli = _criar_cliente(client, cookie_v)
    p, v = _camiseta_pronta(client, cookie_v)
    criado = client.post(
        "/api/pedidos",
        cookies={"texki_session": cookie_v},
        json={
            "cliente_id": cli["id"],
            "data_entrega": _amanha(),
            "itens": [
                {"produto_id": p["id"], "variacao_id": v["id"], "quantidade": "1"}
            ],
        },
    ).json()
    cookie_adm = login(admin)
    r = client.put(
        f"/api/pedidos/{criado['id']}/responsavel",
        cookies={"texki_session": cookie_adm},
        json={"vendedora_id": impressor.id},
    )
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "pedido.responsavel_invalido"


# ---------- RBAC ----------

@pytest.mark.parametrize(
    "metodo,path",
    [
        # CRUD bloqueado pro impressor (Fatia 3).
        ("POST", "/api/pedidos"),
        ("PUT", "/api/pedidos/1"),
        ("DELETE", "/api/pedidos/1"),
    ],
)
def test_pedidos_bloqueia_impressor_no_crud(client, impressor, login, metodo, path):
    cookie = login(impressor)
    body = {} if metodo in ("POST", "PUT") else None
    r = client.request(metodo, path, cookies={"texki_session": cookie}, json=body)
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "auth.forbidden"


def test_pedidos_bloqueia_sem_auth(client):
    r = client.get("/api/pedidos")
    assert r.status_code == 401
