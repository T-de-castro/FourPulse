from pydantic import BaseModel
from typing import Optional


class ClienteBase(BaseModel):
    cpf: str
    nome: str
    cidade: str
    estado: str
    email: Optional[str] = None
    whatsapp: Optional[str] = None
    status: bool = True


class ClienteCreate(ClienteBase):
    pass


class ClienteUpdate(BaseModel):
    nome: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    email: Optional[str] = None
    whatsapp: Optional[str] = None
    status: Optional[bool] = None


class ClienteOut(ClienteBase):
    id: int

    model_config = {"from_attributes": True}
