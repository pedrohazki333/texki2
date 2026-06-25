import pytest
from fastapi import HTTPException

from app.core.deps import require_role
from app.models.usuario import Usuario


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_login_ok(client, vendedora):
    r = client.post(
        "/api/auth/login",
        json={"email": vendedora.email, "senha": "teste123"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["email"] == vendedora.email
    assert body["role"] == "vendedora"
    assert "texki_session" in r.cookies


def test_login_invalido(client, vendedora):
    r = client.post(
        "/api/auth/login",
        json={"email": vendedora.email, "senha": "errada"},
    )
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "auth.invalid_credentials"


def test_login_usuario_inexistente(client):
    r = client.post(
        "/api/auth/login",
        json={"email": "ninguem@test.local", "senha": "x"},
    )
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "auth.invalid_credentials"


def test_me_sem_cookie(client):
    r = client.get("/api/auth/me")
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "auth.unauthenticated"


def test_me_com_cookie(client, vendedora):
    login = client.post(
        "/api/auth/login",
        json={"email": vendedora.email, "senha": "teste123"},
    )
    assert login.status_code == 200
    token = login.cookies.get("texki_session")
    assert token

    r = client.get("/api/auth/me", cookies={"texki_session": token})
    assert r.status_code == 200
    assert r.json()["email"] == vendedora.email
    assert r.json()["role"] == "vendedora"


def test_require_role_bloqueia_papel_errado():
    checker = require_role("administrador")
    fake = Usuario(
        id=1,
        email="x@x.x",
        senha_hash="",
        nome="X",
        role="vendedora",
        ativo=True,
    )
    with pytest.raises(HTTPException) as exc:
        checker(fake)
    assert exc.value.status_code == 403
    assert exc.value.detail["code"] == "auth.forbidden"


def test_require_role_aceita_papel_permitido():
    checker = require_role("vendedora", "administrador")
    fake = Usuario(
        id=1,
        email="x@x.x",
        senha_hash="",
        nome="X",
        role="vendedora",
        ativo=True,
    )
    assert checker(fake) is fake
