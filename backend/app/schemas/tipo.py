from typing import Optional

from pydantic import BaseModel


class TipoBase(BaseModel):
    descricao: str


class TipoCreate(TipoBase):
    pass


class TipoUpdate(BaseModel):
    descricao: Optional[str] = None


class TipoOut(TipoBase):
    id_tipo: int

    model_config = {"from_attributes": True}


# Aliases de compatibilidade
TipoOcorrenciaBase = TipoBase
TipoOcorrenciaCreate = TipoCreate
TipoOcorrenciaUpdate = TipoUpdate
TipoOcorrenciaOut = TipoOut
