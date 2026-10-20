from pydantic import BaseModel, EmailStr
from typing import Optional


class UsuarioBase(BaseModel):
    nome: str
    setor: str
    permissao: str = "operador"
    email: EmailStr
    status: bool = True


class UsuarioCreate(UsuarioBase):
    senha: str


class UsuarioUpdate(BaseModel):
    nome: Optional[str] = None
    setor: Optional[str] = None
    permissao: Optional[str] = None
    email: Optional[EmailStr] = None
    status: Optional[bool] = None


class UsuarioOut(UsuarioBase):
    id: int

    model_config = {"from_attributes": True}
