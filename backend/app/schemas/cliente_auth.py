from pydantic import BaseModel, EmailStr, Field, field_validator


class ClienteRegistro(BaseModel):
    nome: str = Field(..., min_length=1, max_length=255)
    cpf: str = Field(..., min_length=11, max_length=14)
    email: EmailStr
    senha: str = Field(..., min_length=8)

    @field_validator("senha")
    @classmethod
    def validar_senha(cls, v: str) -> str:
        if len(v.strip()) < 8:
            raise ValueError("A senha deve ter no mínimo 8 caracteres.")
        if len(v.encode("utf-8")) > 72:
            raise ValueError("A senha não pode exceder 72 bytes.")
        return v


class ClienteLogin(BaseModel):
    email: EmailStr
    senha: str


class ChamadoClienteCreate(BaseModel):
    descricao: str = Field(..., min_length=1)
    tipo_id: int
