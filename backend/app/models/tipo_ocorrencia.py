from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class TipoOcorrencia(Base):
    __tablename__ = "tipos_ocorrencia"

    id = Column(Integer, primary_key=True, index=True)
    descricao = Column(String, unique=True, nullable=False)

    chamados = relationship("Chamado", back_populates="tipo")
