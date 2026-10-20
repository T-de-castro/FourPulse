from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.chamado import CanalEntrada, Prioridade, StatusChamado
from app.schemas.cidadao import CidadaoOut
from app.schemas.tipo_ocorrencia import TipoOcorrenciaOut
from app.schemas.usuario import UsuarioOut


class ChamadoBase(BaseModel):
    descricao: str
    localizacao: Optional[str] = None
    canal_entrada: CanalEntrada = CanalEntrada.telefone
    prioridade: Optional[Prioridade] = Prioridade.media
    notificacao_email: bool = False
    notificacao_whatsapp: bool = False
    data_limite: Optional[datetime] = None


class ChamadoCreate(ChamadoBase):
    solicitante_id: int
    tipo_id: int
    responsavel_id: Optional[int] = None


class ChamadoUpdate(BaseModel):
    descricao: Optional[str] = None
    localizacao: Optional[str] = None
    canal_entrada: Optional[CanalEntrada] = None
    prioridade: Optional[Prioridade] = None
    status: Optional[StatusChamado] = None
    responsavel_id: Optional[int] = None
    tipo_id: Optional[int] = None
    notificacao_email: Optional[bool] = None
    notificacao_whatsapp: Optional[bool] = None
    data_limite: Optional[datetime] = None
    data_fechamento: Optional[datetime] = None


class ChamadoOut(ChamadoBase):
    id: int
    status: StatusChamado
    data_abertura: datetime
    data_fechamento: Optional[datetime] = None
    solicitante: CidadaoOut
    tipo: TipoOcorrenciaOut
    responsavel: Optional[UsuarioOut] = None

    model_config = {"from_attributes": True}


class DashboardOut(BaseModel):
    abertos: int
    em_atendimento: int
    finalizados: int
    por_tipo: dict[str, int]
    por_prioridade: dict[str, int]
