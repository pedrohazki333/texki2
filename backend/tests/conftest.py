"""Fixtures dos testes.

Os testes rodam contra o Postgres do compose (`docker compose exec api pytest`).
Cada teste roda dentro de uma transação que sofre rollback no teardown, isolando
o estado sem precisar de banco dedicado para testes.
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


@pytest.fixture
def db_session():
    engine = create_engine(settings.database_url)
    connection = engine.connect()
    transaction = connection.begin()
    TestSession = sessionmaker(bind=connection, autoflush=False, autocommit=False)
    session = TestSession()

    def _override():
        yield session

    app.dependency_overrides[get_db] = _override
    try:
        yield session
    finally:
        app.dependency_overrides.pop(get_db, None)
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session):
    return TestClient(app)


@pytest.fixture
def vendedora(db_session) -> Usuario:
    user = Usuario(
        email="vendedora@test.local",
        senha_hash=hash_senha("teste123"),
        nome="Vendedora Teste",
        role="vendedora",
        ativo=True,
    )
    db_session.add(user)
    db_session.flush()
    return user
