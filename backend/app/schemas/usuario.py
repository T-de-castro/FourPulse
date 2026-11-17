from typing import Optional

from pydantic import BaseModel, Field, field_validator


def normalizar_permissao(p: Optional[str]) -> str:
    if not p:
        return "atendente"
    limpo = p.strip().lower()
    mapa = {
        "admin": "administrador",
        "administrador": "administrador",
        "operador": "atendente",
        "atendente": "atendente",
        "consulta": "consulta",
        "leitura": "consulta",
    }
    return mapa.get(limpo, limpo)


class UsuarioBase(BaseModel):
    nome: str = Field(..., min_length=2, max_length=255)
    cpf: str
    permissao: str = "atendente"
    status: bool = True
    email: Optional[str] = None

    @field_validator("permissao")
    @classmethod
    def validar_permissao(cls, v: str) -> str:
        return normalizar_permissao(v)


class UsuarioCreate(UsuarioBase):
    senha: str = Field(..., min_length=8, description="Senha com no mínimo 8 caracteres")

    @field_validator("senha")
    @classmethod
    def validar_senha(cls, v: str) -> str:
        if len(v.strip()) < 8:
            raise ValueError("A senha deve possuir no mínimo 8 caracteres.")
        if len(v.encode("utf-8")) > 72:
            raise ValueError("A senha não pode exceder 72 bytes (limite do algoritmo bcrypt).")
        return v


class UsuarioUpdate(BaseModel):
    nome: Optional[str] = None
    cpf: Optional[str] = None
    permissao: Optional[str] = None
    status: Optional[bool] = None
    email: Optional[str] = None
    senha: Optional[str] = None

    @field_validator("permissao")
    @classmethod
    def validar_permissao(cls, v: Optional[str]) -> Optional[str]:
        return normalizar_permissao(v) if v else v

    @field_validator("senha")
    @classmethod
    def validar_senha(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if len(v.strip()) < 8:
                raise ValueError("A senha deve possuir no mínimo 8 caracteres.")
            if len(v.encode("utf-8")) > 72:
                raise ValueError("A senha não pode exceder 72 bytes.")
        return v


class UsuarioOut(BaseModel):
    id_usuario: int
    nome: str
    cpf: Optional[str] = None  # Mascarado para não-administradores
    permissao: str
    status: bool
    email: Optional[str] = None

    model_config = {"from_attributes": True}
