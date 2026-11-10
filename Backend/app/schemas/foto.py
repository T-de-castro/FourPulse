from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ChamadoFotoOut(BaseModel):
    id_foto: int
    chamado_id: int
    caminho_foto: str
    url_foto: Optional[str] = None
    data_upload: datetime

    model_config = {"from_attributes": True}
