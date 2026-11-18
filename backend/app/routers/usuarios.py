from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.auth import hash_senha
from app.auth.dependencies import apenas_admin, get_usuario_atual
from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioOut, UsuarioUpdate

router = APIRouter(prefix="/usuarios", tags=["Usuários"])


def mascarar_cpf(cpf: str) -> str:
    """Mascara o CPF para usuários sem perfil de administrador (ex: ***.***.***-XX)."""
    if not cpf or len(cpf) < 4:
        return "***.***.***-**"
    digitos = "".join(filter(str.isdigit, cpf))
    if len(digitos) >= 11:
        return f"***.***.***-{digitos[-2:]}"
    return "***.***.***-**"


def preparar_usuario_out(u: Usuario, usuario_solicitante: Usuario) -> UsuarioOut:
    is_admin = usuario_solicitante.permissao.lower() in ["admin", "administrador"]
    cpf_exibicao = u.cpf if is_admin else mascarar_cpf(u.cpf)
    return UsuarioOut(
        id_usuario=u.id_usuario,
        nome=u.nome,
        cpf=cpf_exibicao,
        permissao=u.permissao,
        status=u.status,
        email=u.email,
    )


@router.get("/", response_model=List[UsuarioOut])
def listar_usuarios(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_usuario_atual),
):
    usuarios = db.query(Usuario).offset(skip).limit(limit).all()
    return [preparar_usuario_out(u, usuario_atual) for u in usuarios]


@router.post("/", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
def criar_usuario(
    dados: UsuarioCreate,
    db: Session = Depends(get_db),
    usuario_admin: Usuario = Depends(apenas_admin),
):
    if db.query(Usuario).filter(Usuario.cpf == dados.cpf).first():
        raise HTTPException(status_code=400, detail="CPF já cadastrado")
    if dados.email and db.query(Usuario).filter(Usuario.email == dados.email).first():
        raise HTTPException(status_code=400, detail="E-mail já cadastrado")

    try:
        senha_cripto = hash_senha(dados.senha)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    usuario = Usuario(
        **dados.model_dump(exclude={"senha"}),
        senha_hash=senha_cripto,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return preparar_usuario_out(usuario, usuario_admin)


@router.get("/{id_usuario}", response_model=UsuarioOut)
def buscar_usuario(
    id_usuario: int,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_usuario_atual),
):
    usuario = db.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return preparar_usuario_out(usuario, usuario_atual)


@router.put("/{id_usuario}", response_model=UsuarioOut)
def atualizar_usuario(
    id_usuario: int,
    dados: UsuarioUpdate,
    db: Session = Depends(get_db),
    usuario_admin: Usuario = Depends(apenas_admin),
):
    usuario = db.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    payload = dados.model_dump(exclude_none=True)
    if "senha" in payload:
        nova_senha = payload.pop("senha")
        try:
            usuario.senha_hash = hash_senha(nova_senha)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    for campo, valor in payload.items():
        setattr(usuario, campo, valor)

    db.commit()
    db.refresh(usuario)
    return preparar_usuario_out(usuario, usuario_admin)


@router.delete("/{id_usuario}", status_code=status.HTTP_204_NO_CONTENT)
def desativar_usuario(
    id_usuario: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(apenas_admin),
):
    usuario = db.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    usuario.status = False  # soft delete
    db.commit()
