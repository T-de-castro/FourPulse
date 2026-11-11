from app.models.usuario import Usuario
from app.models.cliente import Cliente
from app.models.tipo import Tipo, TipoOcorrencia
from app.models.chamado import Chamado
from app.models.material import Material, ChamadoMaterial
from app.models.foto import ChamadoFoto

__all__ = [
    "Usuario",
    "Cliente",
    "Tipo",
    "TipoOcorrencia",
    "Chamado",
    "Material",
    "ChamadoMaterial",
    "ChamadoFoto",
]
