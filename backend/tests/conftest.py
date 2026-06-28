"""Fixtures dos testes.

Os testes rodam contra o Postgres do compose (`docker compose exec api pytest`).
Cada teste opera dentro de uma transação externa que sofre rollback no teardown,
isolando o estado sem precisar de banco dedicado para testes. O modo
`create_savepoint` garante que session.commit() feito pelo código sob teste
emite um SAVEPOINT release (e não fecha a transação externa), preservando o
rollback final.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.deps import get_db
from app.core.security import hash_senha
from app.main import app
from app.models.usuario import Usuario


@pytest.fixture(autouse=True)
def uploads_em_tmp(tmp_path, monkeypatch):
    """Aponta o storage para um tmp por teste — não escreve em /srv/texki2."""
    monkeypatch.setattr(settings, "uploads_dir", str(tmp_path))
    yield


@pytest.fixture
def db_session():
    engine = create_engine(settings.database_url)
    connection = engine.connect()
    transaction = connection.begin()
    TestSession = sessionmaker(
        bind=connection,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    session = TestSession()

    def _override():
        yield session

    app.dependency_overrides[get_db] = _override
    try:
        yield session
    finally:
        app.dependency_overrides.pop(get_db, None)
        session.close()
        if transaction.is_active:
            transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session):
    return TestClient(app)


@pytest.fixture
def vendedora(db_session) -> Usuario:
    user = Usuario(
        email="vendedora.teste@livreprint.com",
        senha_hash=hash_senha("teste123"),
        nome="Vendedora Teste",
        role="vendedora",
        ativo=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def admin(db_session) -> Usuario:
    user = Usuario(
        email="admin.teste@livreprint.com",
        senha_hash=hash_senha("teste123"),
        nome="Admin Teste",
        role="administrador",
        ativo=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def impressor(db_session) -> Usuario:
    user = Usuario(
        email="impressor.teste@livreprint.com",
        senha_hash=hash_senha("teste123"),
        nome="Impressor Teste",
        role="impressor",
        ativo=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def login(client):
    """Faz login com o usuário fornecido e devolve o cookie de sessão."""

    def _login(user: Usuario, senha: str = "teste123") -> str:
        r = client.post("/api/auth/login", json={"email": user.email, "senha": senha})
        assert r.status_code == 200, r.text
        cookie = r.cookies.get("texki_session")
        assert cookie, "login não devolveu cookie de sessão"
        return cookie

    return _login
