from pydantic import BaseModel, EmailStr, Field


class ClienteRegistro(BaseModel):
    nome: str = Field(..., min_length=1, max_length=255)
    cpf: str = Field(..., min_length=11, max_length=14)
    email: EmailStr
    senha: str = Field(..., min_length=8)


class ClienteLogin(BaseModel):
    email: EmailStr
    senha: str


class ChamadoClienteCreate(BaseModel):
    descricao: str = Field(..., min_length=1)
    tipo_id: int
