"""Dashboard de pedidos por status (Fatia 4 — RF6)."""
from datetime import date, timedelta

from app.models.cliente import Cliente
from app.models.pedido import Pedido


TELEFONE = "(11) 90000-0001"


def _cli(db_session, nome="Carla") -> Cliente:
    c = Cliente(
        primeiro_nome=nome,
        telefone=TELEFONE,
        consentimento_lgpd=False,
    )
    db_session.add(c)
    db_session.flush()
    return c


def _pedido(db_session, vendedora, status: str) -> Pedido:
    p = Pedido(
        cliente_id=_cli(db_session).id,
        vendedora_id=vendedora.id,
        status=status,
        data_entrega=date.today() + timedelta(days=1),
        total=0,
    )
    db_session.add(p)
    db_session.flush()
    return p


def test_dashboard_agrupa_por_status(client, db_session, vendedora, login):
    cookie = login(vendedora)
    _pedido(db_session, vendedora, "recebido")
    _pedido(db_session, vendedora, "recebido")
    _pedido(db_session, vendedora, "pago")
    _pedido(db_session, vendedora, "entregue")
    db_session.commit()

    r = client.get("/api/pedidos/dashboard", cookies={"texki_session": cookie})
    assert r.status_code == 200, r.text
    body = r.json()
    assert set(body.keys()) == {
        "recebido",
        "pago",
        "na_fila_de_impressao",
        "impressao_pronta",
        "pedido_pronto",
        "entregue",
    }
    assert len(body["recebido"]) >= 2
    assert len(body["pago"]) >= 1
    assert len(body["entregue"]) >= 1


def test_dashboard_oculta_cancelado(client, db_session, vendedora, login):
    cookie = login(vendedora)
    p_cancelado = _pedido(db_session, vendedora, "cancelado")
    p_visivel = _pedido(db_session, vendedora, "recebido")
    db_session.commit()

    r = client.get("/api/pedidos/dashboard", cookies={"texki_session": cookie})
    assert r.status_code == 200
    body = r.json()
    todos_ids = {p["id"] for grupo in body.values() for p in grupo}
    assert p_visivel.id in todos_ids
    assert p_cancelado.id not in todos_ids
    # E a chave "cancelado" não existe no dashboard.
    assert "cancelado" not in body


def test_lista_completa_inclui_cancelado(client, db_session, vendedora, login):
    cookie = login(vendedora)
    p_cancelado = _pedido(db_session, vendedora, "cancelado")
    db_session.commit()

    r = client.get("/api/pedidos", cookies={"texki_session": cookie})
    assert r.status_code == 200
    ids = {p["id"] for p in r.json()}
    assert p_cancelado.id in ids


def test_dashboard_card_traz_cliente_nome_e_primeira_arte(
    client, db_session, vendedora, login
):
    """O card precisa ter cliente_nome e (quando há arte) primeira_arte_id/mime."""
    from app.models.arte import Arte

    cookie = login(vendedora)
    pedido = _pedido(db_session, vendedora, "recebido")
    # Arte com `ordem=1` é a "primeira"; coloco uma `ordem=2` antes pra garantir
    # que a ordenação não pega pela inserção.
    db_session.add(
        Arte(
            pedido_id=pedido.id,
            arquivo_path="x_segunda.png",
            arquivo_mime="image/png",
            largura_cm=10,
            altura_cm=10,
            ordem=2,
        )
    )
    db_session.add(
        Arte(
            pedido_id=pedido.id,
            arquivo_path="x_primeira.png",
            arquivo_mime="image/png",
            largura_cm=10,
            altura_cm=10,
            ordem=1,
        )
    )
    db_session.commit()

    r = client.get("/api/pedidos/dashboard", cookies={"texki_session": cookie})
    body = r.json()
    card = next(c for c in body["recebido"] if c["id"] == pedido.id)
    assert "Carla" in card["cliente_nome"]
    assert card["primeira_arte_mime"] == "image/png"
    assert card["primeira_arte_id"] is not None


def test_dashboard_card_sem_arte_traz_primeira_arte_id_none(
    client, db_session, vendedora, login
):
    cookie = login(vendedora)
    pedido = _pedido(db_session, vendedora, "recebido")
    db_session.commit()

    r = client.get("/api/pedidos/dashboard", cookies={"texki_session": cookie})
    body = r.json()
    card = next(c for c in body["recebido"] if c["id"] == pedido.id)
    assert card["primeira_arte_id"] is None
    assert card["primeira_arte_mime"] is None


def test_dashboard_libera_impressor(client, db_session, vendedora, impressor, login):
    _pedido(db_session, vendedora, "recebido")
    db_session.commit()
    cookie = login(impressor)
    r = client.get("/api/pedidos/dashboard", cookies={"texki_session": cookie})
    assert r.status_code == 200


def test_dashboard_bloqueia_sem_auth(client):
    r = client.get("/api/pedidos/dashboard")
    assert r.status_code == 401
