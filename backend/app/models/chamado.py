import enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


class CanalEntrada(str, enum.Enum):
    WHATSAPP = "WhatsApp"
    EMAIL = "E-mail"
    TELEFONE = "Telefone"
    PORTAL = "Portal"
    PRESENCIALMENTE = "Presencialmente"


class StatusChamado(str, enum.Enum):
    ABERTO = "Em aberto"
    EM_ANDAMENTO = "Em andamento"
    AGUARDANDO_RETORNO = "Aguardando retorno"
    FINALIZADO = "Finalizado"


class Chamado(Base):
    __tablename__ = "chamados"

    id_chamado = Column(Integer, primary_key=True, index=True)
    descricao = Column(Text, nullable=False)
    canal_entrada = Column(String(50), nullable=False, default=CanalEntrada.WHATSAPP.value)
    status = Column(String(100), nullable=False, default=StatusChamado.ABERTO.value)
    data_abertura = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    data_limite = Column(DateTime(timezone=True), nullable=True)
    data_fechamento = Column(DateTime(timezone=True), nullable=True)
    notificar_email = Column(Boolean, default=False, nullable=False)
    notificar_whatsapp = Column(Boolean, default=False, nullable=False)

    # Chaves estrangeiras conforme banco.sql
    cliente_id = Column(Integer, ForeignKey("clientes.id_cliente"), nullable=False)
    tipo_id = Column(Integer, ForeignKey("tipos.id_tipo"), nullable=False)

    # Relacionamentos
    cliente = relationship("Cliente", back_populates="chamados")
    tipo = relationship("Tipo", back_populates="chamados")
    fotos = relationship(
        "ChamadoFoto",
        back_populates="chamado",
        cascade="all, delete-orphan",
    )
    materiais = relationship(
        "ChamadoMaterial",
        back_populates="chamado",
        cascade="all, delete-orphan",
    )

    # Propriedades de conveniência para suportar id_cliente / id_tipo
    @property
    def id_cliente(self):
        return self.cliente_id

    @property
    def id_tipo(self):
        return self.tipo_id
