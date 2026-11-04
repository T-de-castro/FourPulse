from app.routers import auth, chamados, clientes, tipos, usuarios

# Alias de compatibilidade
tipos_ocorrencia = tipos

__all__ = ["auth", "chamados", "clientes", "tipos", "tipos_ocorrencia", "usuarios"]
