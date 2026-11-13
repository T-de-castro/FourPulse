from app.routers import auth, chamados, clientes, cliente_conta, materiais, tipos, usuarios

# Alias de compatibilidade
tipos_ocorrencia = tipos

__all__ = ["auth", "chamados", "clientes", "cliente_conta", "materiais", "tipos", "tipos_ocorrencia", "usuarios"]
