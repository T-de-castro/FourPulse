from datetime import datetime
from typing import Optional

from pydantic import BaseModel, model_validator

from app.models.chamado import CanalEntrada, StatusChamado
from app.schemas.cliente import ClienteOut
from app.schemas.tipo import TipoOut


def normalizar_status(status_str: Optional[str]) -> Optional[str]:
    if not status_str:
        return status_str
    mapa = {
        "chamados abertos": StatusChamado.ABERTO.value,
        "aberto": StatusChamado.ABERTO.value,
        "em aberto": StatusChamado.ABERTO.value,
        "em andamento": StatusChamado.EM_ANDAMENTO.value,
        "em_atendimento": StatusChamado.EM_ANDAMENTO.value,
        "aguardando retorno": StatusChamado.AGUARDANDO_RETORNO.value,
        "finalizado": StatusChamado.FINALIZADO.value,
    }
    return mapa.get(status_str.strip().lower(), status_str)


def normalizar_canal(canal_str: Optional[str]) -> Optional[str]:
    if not canal_str:
        return canal_str
    mapa = {
        "whatsapp": CanalEntrada.WHATSAPP.value,
        "e-mail": CanalEntrada.EMAIL.value,
        "email": CanalEntrada.EMAIL.value,
        "portal": CanalEntrada.PORTAL.value,
        "presencialmente": CanalEntrada.PRESENCIALMENTE.value,
        "presencial": CanalEntrada.PRESENCIALMENTE.value,
        "telefone": CanalEntrada.WHATSAPP.value,  # fallback amigável para check constraint
    }
    return mapa.get(canal_str.strip().lower(), canal_str)


class ChamadoBase(BaseModel):
    descricao: str
    canal_entrada: str = CanalEntrada.WHATSAPP.value
    status: str = StatusChamado.ABERTO.value
    notificar_email: bool = False
    notificar_whatsapp: bool = False
    data_limite: Optional[datetime] = None


class ChamadoCreate(ChamadoBase):
    cliente_id: Optional[int] = None
    tipo_id: Optional[int] = None
    id_cliente: Optional[int] = None
    id_tipo: Optional[int] = None

    @model_validator(mode="before")
    @classmethod
    def reconcile_fields(cls, values: dict):
        if isinstance(values, dict):
            # Garante que cliente_id e tipo_id estejam preenchidos
            c_id = values.get("cliente_id") or values.get("id_cliente")
            t_id = values.get("tipo_id") or values.get("id_tipo")
            values["cliente_id"] = c_id
            values["id_cliente"] = c_id
            values["tipo_id"] = t_id
            values["id_tipo"] = t_id
            if "status" in values:
                values["status"] = normalizar_status(values.get("status"))
            if "canal_entrada" in values:
                values["canal_entrada"] = normalizar_canal(values.get("canal_entrada"))
        return values


class ChamadoUpdate(BaseModel):
    descricao: Optional[str] = None
    canal_entrada: Optional[str] = None
    status: Optional[str] = None
    tipo_id: Optional[int] = None
    id_tipo: Optional[int] = None
    notificar_email: Optional[bool] = None
    notificar_whatsapp: Optional[bool] = None
    data_limite: Optional[datetime] = None
    data_fechamento: Optional[datetime] = None

    @model_validator(mode="before")
    @classmethod
    def reconcile_update_fields(cls, values: dict):
        if isinstance(values, dict):
            t_id = values.get("tipo_id") or values.get("id_tipo")
            if t_id is not None:
                values["tipo_id"] = t_id
                values["id_tipo"] = t_id
            if "status" in values and values.get("status") is not None:
                values["status"] = normalizar_status(values.get("status"))
            if "canal_entrada" in values and values.get("canal_entrada") is not None:
                values["canal_entrada"] = normalizar_canal(values.get("canal_entrada"))
        return values


class ChamadoOut(ChamadoBase):
    id_chamado: int
    cliente_id: int
    tipo_id: int
    id_cliente: int
    id_tipo: int
    status: str
    data_abertura: datetime
    data_fechamento: Optional[datetime] = None
    cliente: ClienteOut
    tipo: TipoOut

    model_config = {"from_attributes": True}


class DashboardOut(BaseModel):
    abertos: int
    em_andamento: int
    aguardando_retorno: int
    finalizados: int
    total: int
    por_tipo: dict[str, int]
