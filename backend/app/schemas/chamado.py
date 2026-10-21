from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.chamado import CanalEntrada, StatusChamado
from app.schemas.cliente import ClienteOut
from app.schemas.tipo_ocorrencia import TipoOcorrenciaOut


class ChamadoBase(BaseModel):
    descricao: str
    canal_entrada: CanalEntrada = CanalEntrada.telefone
    notificar_email: bool = False
    notificar_whatsapp: bool = False
    data_limite: Optional[datetime] = None


class ChamadoCreate(ChamadoBase):
    cliente_id: int
    tipo_id: int


class ChamadoUpdate(BaseModel):
    descricao: Optional[str] = None
    canal_entrada: Optional[CanalEntrada] = None
    status: Optional[StatusChamado] = None
    tipo_id: Optional[int] = None
    notificar_email: Optional[bool] = None
    notificar_whatsapp: Optional[bool] = None
    data_limite: Optional[datetime] = None
    data_fechamento: Optional[datetime] = None


class ChamadoOut(ChamadoBase):
    id: int
    status: StatusChamado
    data_abertura: datetime
    data_fechamento: Optional[datetime] = None
    cliente: ClienteOut
    tipo: TipoOcorrenciaOut

    model_config = {"from_attributes": True}


class DashboardOut(BaseModel):
    abertos: int
    em_atendimento: int
    finalizados: int
    por_tipo: dict[str, int]
