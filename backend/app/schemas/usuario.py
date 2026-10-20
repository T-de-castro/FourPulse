from pydantic import BaseModel
from typing import Optional


class UsuarioBase(BaseModel):
    nome: str
    cpf: str
    permissao: str = "operador"
    status: bool = True
    email: Optional[str] = None  # usado para login


class UsuarioCreate(UsuarioBase):
    senha: str


class UsuarioUpdate(BaseModel):
    nome: Optional[str] = None
    cpf: Optional[str] = None
    permissao: Optional[str] = None
    status: Optional[bool] = None
    email: Optional[str] = None


class UsuarioOut(UsuarioBase):
    id: int

    model_config = {"from_attributes": True}
