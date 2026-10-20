from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import auth, chamados, clientes, tipos_ocorrencia, usuarios

# Cria as tabelas automaticamente se não existirem
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FourPulse API",
    description="Sistema de Controle de Chamados — Defesa Civil",
    version="1.0.0",
)

# Permite requisições do Streamlit rodando localmente
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, trocar pelo domínio do frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registra os routers
app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(clientes.router)
app.include_router(tipos_ocorrencia.router)
app.include_router(chamados.router)


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "app": "FourPulse API"}
