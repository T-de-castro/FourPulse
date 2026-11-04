from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Tipo(Base):
    __tablename__ = "tipos"

    id_tipo = Column(Integer, primary_key=True, index=True)
    descricao = Column(String(255), nullable=False)

    chamados = relationship("Chamado", back_populates="tipo")


# Alias de compatibilidade
TipoOcorrencia = Tipo
