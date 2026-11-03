from datetime import datetime
from typing import Optional

from pydantic import BaseModel, model_validator

from app.models.chamado import CanalEntrada, StatusChamado
from app.schemas.cliente import ClienteOut
from app.schemas.tipo_ocorrencia import TipoOcorrenciaOut


class ChamadoBase(BaseModel):
    descricao: str
    canal_entrada: str = CanalEntrada.TELEFONE.value
    notificar_email: bool = False
    notificar_whatsapp: bool = False
    data_limite: Optional[datetime] = None


class ChamadoCreate(ChamadoBase):
    id_cliente: Optional[int] = None
    id_tipo: Optional[int] = None
    # Suporte para compatibilidade se enviarem cliente_id / tipo_id
    cliente_id: Optional[int] = None
    tipo_id: Optional[int] = None

    @model_validator(mode="before")
    @classmethod
    def reconcile_ids(cls, values: dict):
        if isinstance(values, dict):
            if "id_cliente" not in values or values.get("id_cliente") is None:
                values["id_cliente"] = values.get("cliente_id")
            if "id_tipo" not in values or values.get("id_tipo") is None:
                values["id_tipo"] = values.get("tipo_id")
        return values


class ChamadoUpdate(BaseModel):
    descricao: Optional[str] = None
    canal_entrada: Optional[str] = None
    status: Optional[str] = None
    id_tipo: Optional[int] = None
    tipo_id: Optional[int] = None
    notificar_email: Optional[bool] = None
    notificar_whatsapp: Optional[bool] = None
    data_limite: Optional[datetime] = None
    data_fechamento: Optional[datetime] = None

    @model_validator(mode="before")
    @classmethod
    def reconcile_update_ids(cls, values: dict):
        if isinstance(values, dict):
            if values.get("id_tipo") is None and values.get("tipo_id") is not None:
                values["id_tipo"] = values.get("tipo_id")
        return values


class ChamadoOut(ChamadoBase):
    id_chamado: int
    id_cliente: int
    id_tipo: int
    status: str
    data_abertura: datetime
    data_fechamento: Optional[datetime] = None
    cliente: ClienteOut
    tipo: TipoOcorrenciaOut

    model_config = {"from_attributes": True}


class DashboardOut(BaseModel):
    abertos: int
    em_andamento: int
    aguardando_retorno: int
    finalizados: int
    total: int
    por_tipo: dict[str, int]
