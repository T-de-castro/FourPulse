from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.database import Base


class ChamadoFoto(Base):
    __tablename__ = "chamado_fotos"

    id_foto = Column(Integer, primary_key=True, index=True)
    chamado_id = Column(
        Integer,
        ForeignKey("chamados.id_chamado", ondelete="CASCADE"),
        nullable=False,
    )
    caminho_foto = Column(String(500), nullable=False)
    data_upload = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    chamado = relationship("Chamado", back_populates="fotos")

    @property
    def id_chamado(self):
        return self.chamado_id

    @property
    def url_foto(self):
        caminho = self.caminho_foto or ""
        return f"/{caminho.lstrip('/')}"
