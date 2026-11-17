from sqlalchemy import Boolean, Column, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class Material(Base):
    __tablename__ = "materiais"

    id_material = Column(Integer, primary_key=True, index=True)
    descricao = Column(String(255), nullable=False)
    unidade_medida = Column(String(50), nullable=False)
    valor = Column(Numeric(10, 2), default=0.00, nullable=False)
    status = Column(Boolean, default=True, nullable=False)

    # Relacionamento com vínculos de chamados
    chamados_vinculados = relationship(
        "ChamadoMaterial",
        back_populates="material",
        cascade="all, delete-orphan",
    )


class ChamadoMaterial(Base):
    __tablename__ = "chamado_materiais"

    id_chamado_material = Column(Integer, primary_key=True, index=True)
    chamado_id = Column(
        Integer,
        ForeignKey("chamados.id_chamado", ondelete="CASCADE"),
        nullable=False,
    )
    material_id = Column(
        Integer,
        ForeignKey("materiais.id_material"),
        nullable=False,
    )
    quantidade = Column(Numeric(10, 2), nullable=False)

    __table_args__ = (
        UniqueConstraint("chamado_id", "material_id", name="uq_chamado_material"),
    )

    # Relacionamentos
    chamado = relationship("Chamado", back_populates="materiais")
    material = relationship("Material", back_populates="chamados_vinculados")

    @property
    def id_chamado(self):
        return self.chamado_id

    @property
    def id_material_fk(self):
        return self.material_id
