import enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


class CanalEntrada(str, enum.Enum):
    WHATSAPP = "WhatsApp"
    EMAIL = "E-mail"
    TELEFONE = "Telefone"
    PORTAL = "Portal"


class StatusChamado(str, enum.Enum):
    ABERTO = "Chamados abertos"
    EM_ANDAMENTO = "Em andamento"
    AGUARDANDO_RETORNO = "Aguardando retorno"
    FINALIZADO = "Finalizado"


class Chamado(Base):
    __tablename__ = "chamados"

    id_chamado = Column(Integer, primary_key=True, index=True)
    descricao = Column(String, nullable=False)
    canal_entrada = Column(String(50), nullable=False, default=CanalEntrada.TELEFONE.value)
    status = Column(String(50), nullable=False, default=StatusChamado.ABERTO.value)
    notificar_email = Column(Boolean, default=False)
    notificar_whatsapp = Column(Boolean, default=False)

    # Datas
    data_abertura = Column(DateTime(timezone=True), server_default=func.now())
    data_limite = Column(DateTime(timezone=True), nullable=True)
    data_fechamento = Column(DateTime(timezone=True), nullable=True)

    # Chaves estrangeiras (padronizadas conforme diagrama: id_cliente, id_tipo)
    id_cliente = Column(Integer, ForeignKey("clientes.id_cliente"), nullable=False)
    id_tipo = Column(Integer, ForeignKey("tipos_ocorrencia.id_tipo"), nullable=False)

    # Relacionamentos
    cliente = relationship("Cliente", back_populates="chamados")
    tipo = relationship("TipoOcorrencia", back_populates="chamados")
