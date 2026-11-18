from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.auth.dependencies import get_usuario_ou_cliente
from app.config import settings
from app.database import Base, engine, get_db
from app.models.chamado import Chamado
from app.models.foto import ChamadoFoto
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


# Endpoint protegido para acesso a fotos salvas em uploads (Atividade B)
@app.get("/uploads/{caminho:path}", tags=["Arquivos Protegidos"])
def download_arquivo_protegido(
    caminho: str,
    db: Session = Depends(get_db),
    auth_ctx: dict = Depends(get_usuario_ou_cliente),
):
    """
    Entrega arquivos físicos de uploads com autenticação e autorização obrigatórias.
    - Bloqueia acesso anônimo sem token (HTTP 401).
    - Para clientes: valida se a foto pertence ao chamado daquele cliente (HTTP 403 se for de outro).
    - Para staff interno: acesso liberado.
    """
    caminho_relativo = f"uploads/{caminho.lstrip('/')}"
    arquivo_path = Path(caminho_relativo)

    if not arquivo_path.exists() or not arquivo_path.is_file():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado no servidor")

    # Se for cliente, valida a propriedade do chamado
    if auth_ctx.get("tipo") == "cliente":
        foto = db.query(ChamadoFoto).filter(ChamadoFoto.caminho_foto == caminho_relativo).first()
        if foto:
            chamado = db.query(Chamado).filter(Chamado.id_chamado == foto.chamado_id).first()
            if not chamado or chamado.cliente_id != auth_ctx.get("id_cliente"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Acesso negado. Esta foto pertence ao chamado de outro cliente.",
                )

    ext = arquivo_path.suffix.lower()
    media_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }
    media_type = media_types.get(ext, "application/octet-stream")

    return FileResponse(
        path=arquivo_path,
        media_type=media_type,
        filename=arquivo_path.name,
        headers={"X-Content-Type-Options": "nosniff"},
    )


# Registra os routers
app.include_router(auth.router)
app.include_router(cliente_conta.router)
app.include_router(usuarios.router)
app.include_router(clientes.router)
app.include_router(tipos.router)
app.include_router(materiais.router)
app.include_router(chamados.router)
app.include_router(pluviometria.router)


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "app": "FourPulse API"}
