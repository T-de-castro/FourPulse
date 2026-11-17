from app.routers import (
    auth,
    chamados,
    cliente_conta,
    clientes,
    materiais,
    pluviometria,
    tipos,
    usuarios,
)

# Alias de compatibilidade
tipos_ocorrencia = tipos

__all__ = [
    "auth",
    "chamados",
    "cliente_conta",
    "clientes",
    "materiais",
    "pluviometria",
    "tipos",
    "tipos_ocorrencia",
    "usuarios",
]
