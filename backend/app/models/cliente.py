from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Cliente(Base):
    __tablename__ = "clientes"

    id_cliente = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=False)
    cpf = Column(String(14), unique=True, nullable=False, index=True)
    cidade = Column(String(100), nullable=False)
    estado = Column(String(2), nullable=False)
    email = Column(String(150), nullable=True)
    whatsapp = Column(String(20), nullable=True)
    status = Column(Boolean, default=True)

    chamados = relationship("Chamado", back_populates="cliente")
