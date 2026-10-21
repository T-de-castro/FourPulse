from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Cidadao(Base):
    __tablename__ = "cidadaos"

    id = Column(Integer, primary_key=True, index=True)
    cpf = Column(String(14), unique=True, nullable=False, index=True)
    nome = Column(String, nullable=False)
    cidade = Column(String, nullable=False)
    estado = Column(String(2), nullable=False)
    endereco = Column(String, nullable=True)
    email = Column(String, nullable=True)
    whatsapp = Column(String(20), nullable=True)
    status = Column(Boolean, default=True)

    # Chamados feitos por este cidadão
    chamados = relationship("Chamado", back_populates="solicitante")
