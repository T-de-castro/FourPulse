from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from app.schemas.material import MaterialOut


class ChamadoMaterialBase(BaseModel):
    quantidade: Decimal = Field(..., gt=0, description="Quantidade utilizada do material (deve ser maior que zero)")


class ChamadoMaterialCreate(ChamadoMaterialBase):
    material_id: Optional[int] = None
    id_material: Optional[int] = None

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
    material: Optional[MaterialOut] = None

    model_config = {"from_attributes": True}
