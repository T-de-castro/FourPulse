from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class MaterialBase(BaseModel):
    descricao: str = Field(..., min_length=1, max_length=255, description="Descrição do material (ex: Lona 4x4, Cesta Básica, Telha 6mm)")
    unidade_medida: str = Field(..., min_length=1, max_length=50, description="Unidade de medida (ex: UN, M², KG, CX)")
    valor: Decimal = Field(default=Decimal("0.00"), ge=0, description="Valor unitário estimado do material (R$)")
    status: bool = True


class MaterialCreate(MaterialBase):
    pass


class MaterialUpdate(BaseModel):
    descricao: Optional[str] = Field(None, min_length=1, max_length=255)
    unidade_medida: Optional[str] = Field(None, min_length=1, max_length=50)
    valor: Optional[Decimal] = Field(None, ge=0)
    status: Optional[bool] = None


class MaterialOut(MaterialBase):
    id_material: int

    model_config = {"from_attributes": True}
