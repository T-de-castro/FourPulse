from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_usuario_atual
from app.database import get_db
from app.models.cidadao import Cidadao
from app.models.usuario import Usuario
from app.schemas.cidadao import CidadaoCreate, CidadaoOut, CidadaoUpdate

router = APIRouter(prefix="/cidadaos", tags=["Cidadãos"])


@router.get("/", response_model=List[CidadaoOut])
def listar_cidadaos(
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_usuario_atual),
):
    return db.query(Cidadao).all()


@router.post("/", response_model=CidadaoOut, status_code=status.HTTP_201_CREATED)
def criar_cidadao(
    dados: CidadaoCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_usuario_atual),
):
    if db.query(Cidadao).filter(Cidadao.cpf == dados.cpf).first():
        raise HTTPException(status_code=400, detail="CPF já cadastrado")
    cidadao = Cidadao(**dados.model_dump())
    db.add(cidadao)
    db.commit()
    db.refresh(cidadao)
    return cidadao


@router.get("/{cidadao_id}", response_model=CidadaoOut)
def buscar_cidadao(
    cidadao_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_usuario_atual),
):
    cidadao = db.query(Cidadao).filter(Cidadao.id == cidadao_id).first()
    if not cidadao:
        raise HTTPException(status_code=404, detail="Cidadão não encontrado")
    return cidadao


@router.put("/{cidadao_id}", response_model=CidadaoOut)
def atualizar_cidadao(
    cidadao_id: int,
    dados: CidadaoUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_usuario_atual),
):
    cidadao = db.query(Cidadao).filter(Cidadao.id == cidadao_id).first()
    if not cidadao:
        raise HTTPException(status_code=404, detail="Cidadão não encontrado")
    for campo, valor in dados.model_dump(exclude_none=True).items():
        setattr(cidadao, campo, valor)
    db.commit()
    db.refresh(cidadao)
    return cidadao
