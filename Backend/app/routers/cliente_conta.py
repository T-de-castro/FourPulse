import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session, joinedload, selectinload

from app.auth.auth import criar_token, decodificar_token, hash_senha, verificar_senha
from app.auth.dependencies import oauth2_scheme
from app.config import settings
from app.database import get_db
from app.models.chamado import Chamado, CanalEntrada, StatusChamado
from app.models.cliente import Cliente
from app.models.cliente_conta import ClienteConta
from app.models.foto import ChamadoFoto
from app.models.material import ChamadoMaterial
from app.models.tipo import Tipo
from app.models.usuario import Usuario
from app.schemas.chamado import ChamadoOut
from app.schemas.cliente import ClienteOut
from app.schemas.cliente_auth import ChamadoClienteCreate, ClienteLogin, ClienteRegistro
from app.schemas.foto import ChamadoFotoOut
from app.schemas.tipo import TipoOut

router = APIRouter(prefix="/clientes/conta", tags=["Contas de clientes"])
UPLOAD_BASE_DIR = Path("uploads")


def get_cliente_atual(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Cliente:
    payload = decodificar_token(token)
    if not payload or payload.get("tipo") != "cliente":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de cliente inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        cliente_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")

    conta = db.query(ClienteConta).filter(ClienteConta.cliente_id == cliente_id).first()
    cliente = db.query(Cliente).filter(Cliente.id_cliente == cliente_id).first()
    if not conta or not cliente or not cliente.status:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Conta não encontrada ou inativa")
    return cliente


@router.post("/registrar", response_model=ClienteOut, status_code=status.HTTP_201_CREATED)
def registrar_cliente(dados: ClienteRegistro, db: Session = Depends(get_db)):
    cpf = re.sub(r"\D", "", dados.cpf)
    email = dados.email.strip().casefold()
    if db.query(Cliente).filter(Cliente.cpf == cpf).first():
        raise HTTPException(status_code=400, detail="CPF já cadastrado")
    if db.query(ClienteConta).filter(ClienteConta.email == email).first():
        raise HTTPException(status_code=400, detail="E-mail já cadastrado")
    if db.query(Cliente).filter(Cliente.email.ilike(email)).first():
        raise HTTPException(status_code=400, detail="E-mail já cadastrado")
    if db.query(Usuario).filter(Usuario.email.ilike(email)).first():
        raise HTTPException(status_code=400, detail="E-mail já cadastrado")

    cliente = Cliente(
        nome=dados.nome.strip(),
        cpf=cpf,
        email=email,
        cidade=settings.CIDADE_PADRAO,
        estado=settings.ESTADO_PADRAO,
    )
    db.add(cliente)
    db.flush()
    conta = ClienteConta(
        cliente_id=cliente.id_cliente,
        email=email,
        senha_hash=hash_senha(dados.senha),
    )
    db.add(conta)
    db.commit()
    db.refresh(cliente)
    return cliente


@router.post("/login")
def login_cliente(dados: ClienteLogin, db: Session = Depends(get_db)):
    conta = (
        db.query(ClienteConta)
        .filter(ClienteConta.email == dados.email.strip().casefold())
        .first()
    )
    if not conta or not verificar_senha(dados.senha, conta.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    cliente = db.query(Cliente).filter(Cliente.id_cliente == conta.cliente_id).first()
    if not cliente or not cliente.status:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cliente inativo")

    token = criar_token({"sub": str(cliente.id_cliente), "tipo": "cliente"})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=ClienteOut)
def obter_cliente_atual(cliente: Cliente = Depends(get_cliente_atual)):
    return cliente


@router.get("/tipos", response_model=List[TipoOut])
def listar_tipos_cliente(
    db: Session = Depends(get_db),
    _: Cliente = Depends(get_cliente_atual),
):
    return db.query(Tipo).order_by(Tipo.descricao.asc()).all()


@router.get("/chamados", response_model=List[ChamadoOut])
def listar_chamados_cliente(
    db: Session = Depends(get_db),
    cliente: Cliente = Depends(get_cliente_atual),
):
    return (
        db.query(Chamado)
        .options(
            joinedload(Chamado.cliente),
            joinedload(Chamado.tipo),
            selectinload(Chamado.fotos),
            selectinload(Chamado.materiais).joinedload(ChamadoMaterial.material),
        )
        .filter(Chamado.cliente_id == cliente.id_cliente)
        .order_by(Chamado.data_abertura.desc())
        .all()
    )


@router.post("/chamados", response_model=ChamadoOut, status_code=status.HTTP_201_CREATED)
def criar_chamado_cliente(
    dados: ChamadoClienteCreate,
    db: Session = Depends(get_db),
    cliente: Cliente = Depends(get_cliente_atual),
):
    tipo = db.query(Tipo).filter(Tipo.id_tipo == dados.tipo_id).first()
    if not tipo:
        raise HTTPException(status_code=404, detail="Tipo não encontrado")

    chamado = Chamado(
        descricao=dados.descricao.strip(),
        canal_entrada=CanalEntrada.PORTAL.value,
        status=StatusChamado.ABERTO.value,
        cliente_id=cliente.id_cliente,
        tipo_id=dados.tipo_id,
    )
    db.add(chamado)
    db.commit()
    db.refresh(chamado)
    return chamado


@router.post(
    "/chamados/{id_chamado}/fotos",
    response_model=List[ChamadoFotoOut],
    status_code=status.HTTP_201_CREATED,
)
async def enviar_fotos_cliente(
    id_chamado: int,
    fotos: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    cliente: Cliente = Depends(get_cliente_atual),
):
    chamado = (
        db.query(Chamado)
        .filter(
            Chamado.id_chamado == id_chamado,
            Chamado.cliente_id == cliente.id_cliente,
        )
        .first()
    )
    if not chamado:
        raise HTTPException(status_code=404, detail="Chamado não encontrado")
    if not fotos or len(fotos) > 5:
        raise HTTPException(status_code=400, detail="Envie de 1 a 5 fotos")

    pasta_chamado = UPLOAD_BASE_DIR / "chamados" / str(id_chamado)
    pasta_chamado.mkdir(parents=True, exist_ok=True)
    if any(
        Path(arquivo.filename or "foto.jpg").suffix.lower()
        not in {".jpg", ".jpeg", ".png", ".webp"}
        for arquivo in fotos
    ):
        raise HTTPException(status_code=400, detail="Formato de foto não permitido")

    registros = []
    for arquivo in fotos:
        nome_original = arquivo.filename or "foto.jpg"
        nome_seguro = re.sub(r"[^\w.-]", "_", Path(nome_original).name, flags=re.UNICODE)
        nome_final = f"{int(datetime.now(timezone.utc).timestamp())}_{uuid.uuid4().hex[:8]}_{nome_seguro}"
        caminho_completo = pasta_chamado / nome_final
        conteudo = await arquivo.read()
        caminho_completo.write_bytes(conteudo)
        registro = ChamadoFoto(
            chamado_id=id_chamado,
            caminho_foto=f"uploads/chamados/{id_chamado}/{nome_final}",
        )
        db.add(registro)
        registros.append(registro)

    db.commit()
    for registro in registros:
        db.refresh(registro)
    return registros
