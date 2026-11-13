from sqlalchemy import Boolean, Column, Integer, String

from app.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id_usuario = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=False)
    cpf = Column(String(14), unique=True, nullable=False, index=True)
    permissao = Column(String(50), nullable=False, default="operador")
    status = Column(Boolean, default=True)

    # Necessário para autenticação/login
    email = Column(String(150), unique=True, nullable=True, index=True)
    senha_hash = Column("senha", String, nullable=False)
