from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth.auth import criar_token, verificar_senha
from app.auth.dependencies import get_usuario_atual
from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioOut

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.email == form.username).first()
    if not usuario or not verificar_senha(form.password, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not usuario.status:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuário inativo")

    token = criar_token({"sub": str(usuario.id_usuario), "permissao": usuario.permissao})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UsuarioOut)
def usuario_atual(usuario: Usuario = Depends(get_usuario_atual)):
    return usuario
