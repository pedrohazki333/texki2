from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import COOKIE_NAME, get_current_user, get_db
from app.core.security import criar_token, verificar_senha
from app.models.usuario import Usuario
from app.schemas.auth import LoginIn, UsuarioOut

router = APIRouter()


@router.post("/login", response_model=UsuarioOut)
def login(payload: LoginIn, response: Response, db: Session = Depends(get_db)) -> UsuarioOut:
    user = db.scalar(select(Usuario).where(Usuario.email == payload.email))
    if user is None or not user.ativo or not verificar_senha(payload.senha, user.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "auth.invalid_credentials", "message": "E-mail ou senha inválidos."},
        )
    token, _ = criar_token(user.id, user.role)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=settings.jwt_expires_minutes * 60,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
    )
    return UsuarioOut(id=user.id, email=user.email, nome=user.nome, role=user.role)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout() -> Response:
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie(key=COOKIE_NAME, path="/")
    return response


@router.get("/me", response_model=UsuarioOut)
def me(user: Usuario = Depends(get_current_user)) -> UsuarioOut:
    return UsuarioOut(id=user.id, email=user.email, nome=user.nome, role=user.role)
