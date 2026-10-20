from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    setor = Column(String, nullable=False)
    permissao = Column(String, nullable=False, default="operador")  # "admin" ou "operador"
    email = Column(String, unique=True, nullable=False, index=True)
    senha_hash = Column(String, nullable=False)
    status = Column(Boolean, default=True)

    # Chamados atribuídos a este usuário
    chamados = relationship("Chamado", back_populates="responsavel")
