from pydantic import BaseModel
from typing import Optional


class TipoOcorrenciaBase(BaseModel):
    descricao: str


class TipoOcorrenciaCreate(TipoOcorrenciaBase):
    pass


class TipoOcorrenciaUpdate(BaseModel):
    descricao: Optional[str] = None


class TipoOcorrenciaOut(TipoOcorrenciaBase):
    id: int

    model_config = {"from_attributes": True}
