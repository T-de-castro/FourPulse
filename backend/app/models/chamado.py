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


class StatusChamado(str, enum.Enum):
    aberto = "aberto"
    em_atendimento = "em_atendimento"
    finalizado = "finalizado"


class Chamado(Base):
    __tablename__ = "chamados"

    id = Column(Integer, primary_key=True, index=True)
    descricao = Column(String, nullable=False)
    canal_entrada = Column(Enum(CanalEntrada), nullable=False, default=CanalEntrada.telefone)
    status = Column(Enum(StatusChamado), nullable=False, default=StatusChamado.aberto)
    notificar_email = Column(Boolean, default=False)
    notificar_whatsapp = Column(Boolean, default=False)

    # Datas
    data_abertura = Column(DateTime(timezone=True), server_default=func.now())
    data_limite = Column(DateTime(timezone=True), nullable=True)
    data_fechamento = Column(DateTime(timezone=True), nullable=True)

    # Campos mencionados no chat do grupo — não estão no diagrama ER ainda
    # prioridade = Column(Enum(Prioridade), nullable=True)
    # localizacao = Column(String, nullable=True)
    # responsavel_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)

    # Chaves estrangeiras (conforme diagrama)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    tipo_id = Column(Integer, ForeignKey("tipos_ocorrencia.id"), nullable=False)

    # Relacionamentos
    cliente = relationship("Cliente", back_populates="chamados")
    tipo = relationship("TipoOcorrencia", back_populates="chamados")
