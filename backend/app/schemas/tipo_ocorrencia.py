from typing import Optional

from pydantic import BaseModel


class TipoOcorrenciaBase(BaseModel):
    descricao: str


class TipoOcorrenciaCreate(TipoOcorrenciaBase):
    pass


class TipoOcorrenciaUpdate(BaseModel):
    descricao: Optional[str] = None


class TipoOcorrenciaOut(TipoOcorrenciaBase):
    id_tipo: int

    model_config = {"from_attributes": True}
