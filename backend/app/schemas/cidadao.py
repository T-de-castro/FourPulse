from pydantic import BaseModel
from typing import Optional


class CidadaoBase(BaseModel):
    cpf: str
    nome: str
    cidade: str
    estado: str
    endereco: Optional[str] = None
    email: Optional[str] = None
    whatsapp: Optional[str] = None
    status: bool = True


class CidadaoCreate(CidadaoBase):
    pass


class CidadaoUpdate(BaseModel):
    nome: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    endereco: Optional[str] = None
    email: Optional[str] = None
    whatsapp: Optional[str] = None
    status: Optional[bool] = None


class CidadaoOut(CidadaoBase):
    id: int

    model_config = {"from_attributes": True}
