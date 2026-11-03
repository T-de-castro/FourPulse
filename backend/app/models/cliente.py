from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Cliente(Base):
    __tablename__ = "clientes"

    id_cliente = Column(Integer, primary_key=True, index=True)
    cpf = Column(String(14), unique=True, nullable=False, index=True)
    nome = Column(String, nullable=False)
    cidade = Column(String, nullable=False)
    estado = Column(String(2), nullable=False)
    email = Column(String, nullable=True)
    whatsapp = Column(String(20), nullable=True)
    status = Column(String(20), default="Ativo")  # "Ativo", "Inativo"

    # Chamados feitos por este cliente
    chamados = relationship("Chamado", back_populates="cliente")
