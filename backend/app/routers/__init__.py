from app.routers import auth, chamados, clientes, materiais, tipos, usuarios

# Alias de compatibilidade
tipos_ocorrencia = tipos

__all__ = ["auth", "chamados", "clientes", "materiais", "tipos", "tipos_ocorrencia", "usuarios"]
