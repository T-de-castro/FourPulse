from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import apenas_atendente_ou_admin, get_usuario_atual
from app.database import get_db
from app.models.cliente import Cliente
from app.models.usuario import Usuario
from app.schemas.cliente import ClienteCreate, ClienteOut, ClienteUpdate

router = APIRouter(prefix="/clientes", tags=["Clientes"])


@router.get("/", response_model=List[ClienteOut])
def listar_clientes(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_usuario_atual),
):
    return db.query(Cliente).order_by(Cliente.nome.asc()).offset(skip).limit(limit).all()


@router.post("/", response_model=ClienteOut, status_code=status.HTTP_201_CREATED)
def criar_cliente(
    dados: ClienteCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(apenas_atendente_ou_admin),
):
    if db.query(Cliente).filter(Cliente.cpf == dados.cpf).first():
        raise HTTPException(status_code=400, detail="CPF já cadastrado")
    cliente = Cliente(**dados.model_dump())
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return cliente


@router.get("/{id_cliente}", response_model=ClienteOut)
def buscar_cliente(
    id_cliente: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_usuario_atual),
):
    cliente = db.query(Cliente).filter(Cliente.id_cliente == id_cliente).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return cliente


@router.put("/{id_cliente}", response_model=ClienteOut)
def atualizar_cliente(
    id_cliente: int,
    dados: ClienteUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(apenas_atendente_ou_admin),
):
    cliente = db.query(Cliente).filter(Cliente.id_cliente == id_cliente).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    for campo, valor in dados.model_dump(exclude_none=True).items():
        setattr(cliente, campo, valor)
    db.commit()
    db.refresh(cliente)
    return cliente


@router.delete("/{id_cliente}", status_code=status.HTTP_204_NO_CONTENT)
def desativar_cliente(
    id_cliente: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(apenas_atendente_ou_admin),
):
    cliente = db.query(Cliente).filter(Cliente.id_cliente == id_cliente).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    cliente.status = False
    db.commit()
