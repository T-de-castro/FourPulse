from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    cpf = Column(String(14), unique=True, nullable=False, index=True)
    permissao = Column(String, nullable=False, default="operador")  # "admin" ou "operador"
    status = Column(Boolean, default=True)

    # Necessário para autenticação — não está no diagrama mas é obrigatório para login
    email = Column(String, unique=True, nullable=True, index=True)
    senha_hash = Column(String, nullable=False)
