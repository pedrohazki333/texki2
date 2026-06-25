from collections.abc import Callable, Iterator

import jwt as pyjwt
from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import ler_token
from app.db.session import SessionLocal
from app.models.usuario import Usuario

COOKIE_NAME = "texki_session"


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    db: Session = Depends(get_db),
    texki_session: str | None = Cookie(default=None, alias=COOKIE_NAME),
) -> Usuario:
    if not texki_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "auth.unauthenticated", "message": "Sessão ausente."},
        )
    try:
        payload = ler_token(texki_session)
    except pyjwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "auth.unauthenticated", "message": "Sessão inválida ou expirada."},
        )
    user = db.get(Usuario, int(payload["sub"]))
    if user is None or not user.ativo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "auth.unauthenticated", "message": "Usuário inativo ou inexistente."},
        )
    return user


def require_role(*roles: str) -> Callable[[Usuario], Usuario]:
    def _check(user: Usuario = Depends(get_current_user)) -> Usuario:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "auth.forbidden", "message": "Permissão insuficiente."},
            )
        return user

    return _check
