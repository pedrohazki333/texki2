from pydantic import BaseModel, EmailStr


class LoginIn(BaseModel):
    email: EmailStr
    senha: str


class UsuarioOut(BaseModel):
    id: int
    email: EmailStr
    nome: str
    role: str
