from datetime import datetime
from typing import Optional

from pydantic import BaseModel, model_validator


class ChamadoFotoOut(BaseModel):
    id_foto: int
    chamado_id: int
    caminho_foto: str
    url_foto: Optional[str] = None
    data_upload: datetime

    model_config = {"from_attributes": True}

    @model_validator(mode="after")
    def compute_url(self):
        if not self.url_foto:
            self.url_foto = f"/chamados/{self.chamado_id}/fotos/{self.id_foto}/arquivo"
        return self
