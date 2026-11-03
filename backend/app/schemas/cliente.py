from typing import Optional

from pydantic import BaseModel


class ClienteBase(BaseModel):
    cpf: str
    nome: str
    cidade: str
    estado: str
    email: Optional[str] = None
    whatsapp: Optional[str] = None
    status: str = "Ativo"


class ClienteCreate(ClienteBase):
    pass


class ClienteUpdate(BaseModel):
    nome: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    email: Optional[str] = None
    whatsapp: Optional[str] = None
    status: Optional[str] = None


class ClienteOut(ClienteBase):
    id_cliente: int

    model_config = {"from_attributes": True}
