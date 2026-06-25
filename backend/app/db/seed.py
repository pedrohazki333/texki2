from sqlalchemy import select

from app.core.config import settings
from app.core.security import hash_senha
from app.db.session import SessionLocal
from app.models.usuario import Usuario


def seed_admin() -> None:
    with SessionLocal() as db:
        existente = db.scalar(select(Usuario).where(Usuario.email == settings.seed_admin_email))
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


if __name__ == "__main__":
    seed_admin()
