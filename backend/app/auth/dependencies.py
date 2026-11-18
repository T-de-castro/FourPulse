from typing import Optional

from fastapi import Depends, Header, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.auth.auth import decodificar_token
from app.database import get_db
from app.models.cliente import Cliente
from app.models.cliente_conta import ClienteConta
from app.models.usuario import Usuario

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def get_usuario_atual(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticação necessária",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decodificar_token(token)
    if payload is None or payload.get("tipo") == "cliente":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    usuario_id = payload.get("sub")
    usuario = db.query(Usuario).filter(Usuario.id_usuario == usuario_id).first()
    if not usuario or not usuario.status:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado ou inativo",
        )
    return usuario


def apenas_admin(usuario: Usuario = Depends(get_usuario_atual)) -> Usuario:
    if usuario.permissao.lower() not in ["admin", "administrador"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores",
        )
    return usuario


def apenas_atendente_ou_admin(usuario: Usuario = Depends(get_usuario_atual)) -> Usuario:
    papel = usuario.permissao.lower()
    if papel not in ["admin", "administrador", "operador", "atendente"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito. Perfil 'consulta' possui permissão apenas de leitura.",
        )
    return usuario


def get_usuario_ou_cliente(
    authorization: Optional[str] = Header(None),
    token_query: Optional[str] = Query(None, alias="token"),
    db: Session = Depends(get_db),
) -> dict:
    """
    Autentica tanto usuários internos (staff) quanto clientes externos.
    Aceita token via Header 'Authorization: Bearer <token>' ou via Query param '?token=<token>'.
    """
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    elif token_query:
        token = token_query.strip()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação não fornecido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decodificar_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    tipo = payload.get("tipo")
    sub = payload.get("sub")

    if tipo == "cliente":
        try:
            c_id = int(sub)
        except (TypeError, ValueError):
            raise HTTPException(status_code=401, detail="Token de cliente inválido")
        cliente = db.query(Cliente).filter(Cliente.id_cliente == c_id).first()
        conta = db.query(ClienteConta).filter(ClienteConta.cliente_id == c_id).first()
        if not cliente or not conta or not cliente.status:
            raise HTTPException(status_code=401, detail="Conta de cliente inativa ou não encontrada")
        return {"tipo": "cliente", "obj": cliente, "id_cliente": cliente.id_cliente}

    # Usuário interno
    usuario = db.query(Usuario).filter(Usuario.id_usuario == sub).first()
    if not usuario or not usuario.status:
        raise HTTPException(status_code=401, detail="Usuário interno inativo ou não encontrado")
    return {"tipo": "usuario", "obj": usuario, "id_usuario": usuario.id_usuario, "permissao": usuario.permissao}
