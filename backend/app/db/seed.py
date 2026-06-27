from decimal import Decimal

from sqlalchemy import select

from app.core.config import settings
from app.core.security import hash_senha
from app.db.session import SessionLocal
from app.models.faixa_preco import FaixaPreco
from app.models.produto import Produto
from app.models.usuario import Usuario


CATALOGO = [
    {
        "nome": "DTF por metro",
        "tipo": "dtf_por_metro",
        "faixas": [
            ("comprimento_m", "0", "5", "69.90"),
            ("comprimento_m", "5", "10", "59.90"),
            ("comprimento_m", "10", "20", "49.90"),
            ("comprimento_m", "20", None, "39.90"),
        ],
    },
    {
        "nome": "Camiseta",
        "tipo": "vestuario",
        "faixas": [
            ("quantidade", "0", "10", "49.90"),
            ("quantidade", "10", "50", "39.90"),
            ("quantidade", "50", None, "29.90"),
        ],
    },
    {
        "nome": "Blusa de Moletom",
        "tipo": "vestuario",
        "faixas": [
            ("quantidade", "0", "10", "99.90"),
            ("quantidade", "10", "50", "89.90"),
            ("quantidade", "50", None, "79.90"),
        ],
    },
    {
        "nome": "Conjunto Moletom",
        "tipo": "vestuario",
        "faixas": [
            ("quantidade", "0", "10", "149.90"),
            ("quantidade", "10", "50", "139.90"),
            ("quantidade", "50", None, "129.90"),
        ],
    },
]


def seed_admin() -> None:
    with SessionLocal() as db:
        existente = db.scalar(
            select(Usuario).where(Usuario.email == settings.seed_admin_email)
        )
        if existente is not None:
            print(f"[seed] admin já existe: {settings.seed_admin_email}")
            return
        admin = Usuario(
            email=settings.seed_admin_email,
            senha_hash=hash_senha(settings.seed_admin_password),
            nome=settings.seed_admin_nome,
            role="administrador",
            ativo=True,
        )
        db.add(admin)
        db.commit()
        print(f"[seed] admin criado: {settings.seed_admin_email}")


def seed_catalogo() -> None:
    with SessionLocal() as db:
        for entrada in CATALOGO:
            existente = db.scalar(
                select(Produto).where(Produto.nome == entrada["nome"])
            )
            if existente is not None:
                print(f"[seed] produto já existe: {entrada['nome']}")
                continue
            produto = Produto(nome=entrada["nome"], tipo=entrada["tipo"])
            db.add(produto)
            db.flush()
            for base, fmin, fmax, preco in entrada["faixas"]:
                db.add(
                    FaixaPreco(
                        produto_id=produto.id,
                        base=base,
                        min=Decimal(fmin),
                        max=Decimal(fmax) if fmax is not None else None,
                        preco_unitario=Decimal(preco),
                    )
                )
            db.commit()
            print(f"[seed] produto criado: {entrada['nome']}")


if __name__ == "__main__":
    seed_admin()
    seed_catalogo()
