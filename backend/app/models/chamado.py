import enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


class CanalEntrada(str, enum.Enum):
    telefone = "telefone"
    presencial = "presencial"
    web = "web"


class Prioridade(str, enum.Enum):
    baixa = "baixa"
    media = "media"
    alta = "alta"


class StatusChamado(str, enum.Enum):
    aberto = "aberto"
    em_atendimento = "em_atendimento"
    finalizado = "finalizado"


class Chamado(Base):
    __tablename__ = "chamados"

    id = Column(Integer, primary_key=True, index=True)
    descricao = Column(String, nullable=False)
    localizacao = Column(String, nullable=True)
    canal_entrada = Column(Enum(CanalEntrada), nullable=False, default=CanalEntrada.telefone)
    prioridade = Column(Enum(Prioridade), nullable=True, default=Prioridade.media)
    status = Column(Enum(StatusChamado), nullable=False, default=StatusChamado.aberto)
    notificacao_email = Column(Boolean, default=False)
    notificacao_whatsapp = Column(Boolean, default=False)

    # Datas
    data_abertura = Column(DateTime(timezone=True), server_default=func.now())
    data_limite = Column(DateTime(timezone=True), nullable=True)
    data_fechamento = Column(DateTime(timezone=True), nullable=True)

    # Chaves estrangeiras
    solicitante_id = Column(Integer, ForeignKey("cidadaos.id"), nullable=False)
    tipo_id = Column(Integer, ForeignKey("tipos_ocorrencia.id"), nullable=False)
    responsavel_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)

    # Relacionamentos
    solicitante = relationship("Cidadao", back_populates="chamados")
    tipo = relationship("TipoOcorrencia", back_populates="chamados")
    responsavel = relationship("Usuario", back_populates="chamados")
