from datetime import date, datetime, timezone

from app.models.cliente import Cliente


TELEFONE_VALIDO = "(11) 98765-4321"


def _hoje() -> str:
    return datetime.now(timezone.utc).date().isoformat()


# ---------- criação ----------

def test_criar_cliente_minimo(client, vendedora, login):
    cookie = login(vendedora)
    r = client.post(
        "/api/clientes",
        cookies={"texki_session": cookie},
        json={"primeiro_nome": "Maria", "telefone": TELEFONE_VALIDO, "consentimento_lgpd": False},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["primeiro_nome"] == "Maria"
    assert body["ultimo_nome"] is None
    assert body["endereco"] is None
    assert body["telefone"] == TELEFONE_VALIDO
    assert body["consentimento_lgpd"] is False
    assert body["data_consentimento"] is None


def test_criar_cliente_completo_com_consentimento(client, vendedora, login):
    cookie = login(vendedora)
    r = client.post(
        "/api/clientes",
        cookies={"texki_session": cookie},
        json={
            "primeiro_nome": "João",
            "ultimo_nome": "Silva",
            "endereco": "Rua A, 123",
            "telefone": TELEFONE_VALIDO,
            "consentimento_lgpd": True,
        },
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["ultimo_nome"] == "Silva"
    assert body["consentimento_lgpd"] is True
    assert body["data_consentimento"] == _hoje()


def test_criar_cliente_sem_obrigatorio_primeiro_nome(client, vendedora, login):
    cookie = login(vendedora)
    r = client.post(
        "/api/clientes",
        cookies={"texki_session": cookie},
        json={"primeiro_nome": "", "telefone": TELEFONE_VALIDO, "consentimento_lgpd": False},
    )
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "validation.error"


def test_criar_cliente_sem_obrigatorio_telefone(client, vendedora, login):
    cookie = login(vendedora)
    r = client.post(
        "/api/clientes",
        cookies={"texki_session": cookie},
        json={"primeiro_nome": "X", "consentimento_lgpd": False},
    )
    assert r.status_code == 422


def test_criar_cliente_telefone_formato_invalido(client, vendedora, login):
    cookie = login(vendedora)
    r = client.post(
        "/api/clientes",
        cookies={"texki_session": cookie},
        json={
            "primeiro_nome": "X",
            "telefone": "987654321",
            "consentimento_lgpd": False,
        },
    )
    assert r.status_code == 422


def test_criar_cliente_telefone_fixo_aceito(client, vendedora, login):
    """Formato de telefone fixo: (XX) XXXX-XXXX (10 dígitos)."""
    cookie = login(vendedora)
    r = client.post(
        "/api/clientes",
        cookies={"texki_session": cookie},
        json={
            "primeiro_nome": "Empresa",
            "telefone": "(11) 3456-7890",
            "consentimento_lgpd": False,
        },
    )
    assert r.status_code == 201, r.text


# ---------- leitura ----------

def test_listar_clientes_vazio(client, vendedora, login):
    cookie = login(vendedora)
    r = client.get("/api/clientes", cookies={"texki_session": cookie})
    assert r.status_code == 200
    assert r.json() == []


def test_listar_clientes_ordenado_por_nome(client, vendedora, login):
    cookie = login(vendedora)
    for nome in ["Carlos", "Ana", "Beatriz"]:
        client.post(
            "/api/clientes",
            cookies={"texki_session": cookie},
            json={"primeiro_nome": nome, "telefone": TELEFONE_VALIDO, "consentimento_lgpd": False},
        )
    r = client.get("/api/clientes", cookies={"texki_session": cookie})
    nomes = [c["primeiro_nome"] for c in r.json()]
    assert nomes == ["Ana", "Beatriz", "Carlos"]


def test_ver_cliente_inexistente(client, vendedora, login):
    cookie = login(vendedora)
    r = client.get("/api/clientes/99999", cookies={"texki_session": cookie})
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "cliente.not_found"


# ---------- edição (regra LGPD) ----------

def test_editar_marcar_consentimento_grava_data(client, vendedora, login):
    cookie = login(vendedora)
    criado = client.post(
        "/api/clientes",
        cookies={"texki_session": cookie},
        json={"primeiro_nome": "Ana", "telefone": TELEFONE_VALIDO, "consentimento_lgpd": False},
    ).json()
    assert criado["data_consentimento"] is None

    r = client.put(
        f"/api/clientes/{criado['id']}",
        cookies={"texki_session": cookie},
        json={"primeiro_nome": "Ana", "telefone": TELEFONE_VALIDO, "consentimento_lgpd": True},
    )
    assert r.status_code == 200
    assert r.json()["consentimento_lgpd"] is True
    assert r.json()["data_consentimento"] == _hoje()


def test_editar_desmarcar_consentimento_limpa_data(client, vendedora, login):
    cookie = login(vendedora)
    criado = client.post(
        "/api/clientes",
        cookies={"texki_session": cookie},
        json={"primeiro_nome": "Ana", "telefone": TELEFONE_VALIDO, "consentimento_lgpd": True},
    ).json()
    assert criado["data_consentimento"] is not None

    r = client.put(
        f"/api/clientes/{criado['id']}",
        cookies={"texki_session": cookie},
        json={"primeiro_nome": "Ana", "telefone": TELEFONE_VALIDO, "consentimento_lgpd": False},
    )
    assert r.status_code == 200
    assert r.json()["consentimento_lgpd"] is False
    assert r.json()["data_consentimento"] is None


def test_editar_consentimento_ja_marcado_mantem_data_original(
    client, vendedora, login, db_session
):
    cookie = login(vendedora)
    criado = client.post(
        "/api/clientes",
        cookies={"texki_session": cookie},
        json={"primeiro_nome": "Ana", "telefone": TELEFONE_VALIDO, "consentimento_lgpd": True},
    ).json()

    # força data antiga: simula cliente cadastrado há muito tempo
    cliente_db = db_session.get(Cliente, criado["id"])
    cliente_db.data_consentimento = date(2025, 1, 1)
    db_session.commit()

    r = client.put(
        f"/api/clientes/{criado['id']}",
        cookies={"texki_session": cookie},
        json={
            "primeiro_nome": "Ana",
            "endereco": "Rua nova",
            "telefone": TELEFONE_VALIDO,
            "consentimento_lgpd": True,
        },
    )
    assert r.status_code == 200
    assert r.json()["data_consentimento"] == "2025-01-01"


def test_editar_cliente_inexistente(client, vendedora, login):
    cookie = login(vendedora)
    r = client.put(
        "/api/clientes/99999",
        cookies={"texki_session": cookie},
        json={"primeiro_nome": "X", "telefone": TELEFONE_VALIDO, "consentimento_lgpd": False},
    )
    assert r.status_code == 404


def test_editar_validacao_obrigatorio_em_branco(client, vendedora, login):
    cookie = login(vendedora)
    criado = client.post(
        "/api/clientes",
        cookies={"texki_session": cookie},
        json={"primeiro_nome": "Ana", "telefone": TELEFONE_VALIDO, "consentimento_lgpd": False},
    ).json()
    r = client.put(
        f"/api/clientes/{criado['id']}",
        cookies={"texki_session": cookie},
        json={"primeiro_nome": "", "telefone": TELEFONE_VALIDO, "consentimento_lgpd": False},
    )
    assert r.status_code == 422


# ---------- exclusão ----------

def test_excluir_cliente(client, vendedora, login):
    cookie = login(vendedora)
    criado = client.post(
        "/api/clientes",
        cookies={"texki_session": cookie},
        json={"primeiro_nome": "Ana", "telefone": TELEFONE_VALIDO, "consentimento_lgpd": False},
    ).json()

    r = client.delete(f"/api/clientes/{criado['id']}", cookies={"texki_session": cookie})
    assert r.status_code == 204

    consulta = client.get(f"/api/clientes/{criado['id']}", cookies={"texki_session": cookie})
    assert consulta.status_code == 404


def test_excluir_cliente_inexistente(client, vendedora, login):
    cookie = login(vendedora)
    r = client.delete("/api/clientes/99999", cookies={"texki_session": cookie})
    assert r.status_code == 404


# ---------- RBAC ----------

def test_clientes_bloqueia_impressor(client, impressor, login):
    cookie = login(impressor)
    for chamada in [
        lambda: client.get("/api/clientes", cookies={"texki_session": cookie}),
        lambda: client.post(
            "/api/clientes",
            cookies={"texki_session": cookie},
            json={"primeiro_nome": "X", "telefone": TELEFONE_VALIDO, "consentimento_lgpd": False},
        ),
        lambda: client.get("/api/clientes/1", cookies={"texki_session": cookie}),
        lambda: client.put(
            "/api/clientes/1",
            cookies={"texki_session": cookie},
            json={"primeiro_nome": "X", "telefone": TELEFONE_VALIDO, "consentimento_lgpd": False},
        ),
        lambda: client.delete("/api/clientes/1", cookies={"texki_session": cookie}),
    ]:
        r = chamada()
        assert r.status_code == 403, r.text
        assert r.json()["error"]["code"] == "auth.forbidden"


def test_clientes_administrador_pode_criar(client, admin, login):
    cookie = login(admin)
    r = client.post(
        "/api/clientes",
        cookies={"texki_session": cookie},
        json={"primeiro_nome": "Adm", "telefone": TELEFONE_VALIDO, "consentimento_lgpd": False},
    )
    assert r.status_code == 201


def test_clientes_bloqueia_sem_auth(client):
    for chamada in [
        lambda: client.get("/api/clientes"),
        lambda: client.post(
            "/api/clientes",
            json={"primeiro_nome": "X", "telefone": TELEFONE_VALIDO, "consentimento_lgpd": False},
        ),
        lambda: client.get("/api/clientes/1"),
        lambda: client.put(
            "/api/clientes/1",
            json={"primeiro_nome": "X", "telefone": TELEFONE_VALIDO, "consentimento_lgpd": False},
        ),
        lambda: client.delete("/api/clientes/1"),
    ]:
        r = chamada()
        assert r.status_code == 401
        assert r.json()["error"]["code"] == "auth.unauthenticated"
