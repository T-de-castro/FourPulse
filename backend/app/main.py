from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
from app.config import settings
from app.routers import auth, chamados, clientes, cliente_conta, materiais, tipos, usuarios

# Garante que a pasta de uploads físicos exista
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Cria as tabelas automaticamente se não existirem
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FourPulse API",
    description="Sistema de Controle de Chamados — Defesa Civil",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir fotos armazenadas localmente para front-end e consulta
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# Registra os routers
app.include_router(auth.router)
app.include_router(cliente_conta.router)
app.include_router(usuarios.router)
app.include_router(clientes.router)
app.include_router(tipos.router)
app.include_router(materiais.router)
app.include_router(chamados.router)


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "app": "FourPulse API"}
