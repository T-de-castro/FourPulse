from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from app.schemas.material import MaterialOut


class ChamadoMaterialBase(BaseModel):
    quantidade: Decimal = Field(..., gt=0, description="Quantidade utilizada do material (deve ser maior que zero)")


class ChamadoMaterialCreate(ChamadoMaterialBase):
    material_id: Optional[int] = None
    id_material: Optional[int] = None
    idempotency_key: Optional[str] = Field(None, description="Chave de idempotência para evitar duplicidade em retentativas de rede")

    @model_validator(mode="before")
    @classmethod
    def reconcile_material_id(cls, values: dict):
        if isinstance(values, dict):
            m_id = values.get("material_id") or values.get("id_material")
            values["material_id"] = m_id
            values["id_material"] = m_id
        return values


class ChamadoMaterialUpdate(BaseModel):
    quantidade: Decimal = Field(..., gt=0, description="Nova quantidade do material")


class ChamadoMaterialOut(BaseModel):
    id_chamado_material: int
    chamado_id: int
    material_id: int
    quantidade: Decimal
    valor_unitario: Decimal = Field(default=Decimal("0.00"), description="Preço histórico congelado no momento do atendimento")
    valor_catalogo_atual: Optional[Decimal] = Field(None, description="Preço atual de reposição no catálogo")
    subtotal: Optional[Decimal] = Field(None, description="Custo histórico total (quantidade * valor_unitario)")
    material: Optional[MaterialOut] = None

    model_config = {"from_attributes": True}

    @model_validator(mode="after")
    def compute_fields(self):
        if self.material and hasattr(self.material, "valor"):
            self.valor_catalogo_atual = self.material.valor
        # Se valor_unitario histórico foi gravado, calcula subtotal
        v_unit = self.valor_unitario if self.valor_unitario > 0 else (self.valor_catalogo_atual or Decimal("0.00"))
        self.subtotal = Decimal(str(round(float(self.quantidade) * float(v_unit), 2)))
        return self
