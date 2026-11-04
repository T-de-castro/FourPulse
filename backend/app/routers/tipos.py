from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import apenas_admin, get_usuario_atual
from app.database import get_db
from app.models.tipo import Tipo
from app.models.usuario import Usuario
from app.schemas.tipo import TipoCreate, TipoOut, TipoUpdate

router = APIRouter(prefix="/tipos", tags=["Tipos"])


@router.get("/", response_model=List[TipoOut])
def listar_tipos(
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_usuario_atual),
):
    return db.query(Tipo).all()


@router.post("/", response_model=TipoOut, status_code=status.HTTP_201_CREATED)
def criar_tipo(
    dados: TipoCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(apenas_admin),
):
    tipo = Tipo(**dados.model_dump())
    db.add(tipo)
    db.commit()
    db.refresh(tipo)
    return tipo


@router.get("/{id_tipo}", response_model=TipoOut)
def buscar_tipo(
    id_tipo: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_usuario_atual),
):
    tipo = db.query(Tipo).filter(Tipo.id_tipo == id_tipo).first()
    if not tipo:
        raise HTTPException(status_code=404, detail="Tipo não encontrado")
    return tipo


@router.put("/{id_tipo}", response_model=TipoOut)
def atualizar_tipo(
    id_tipo: int,
    dados: TipoUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(apenas_admin),
):
    tipo = db.query(Tipo).filter(Tipo.id_tipo == id_tipo).first()
    if not tipo:
        raise HTTPException(status_code=404, detail="Tipo não encontrado")
    for campo, valor in dados.model_dump(exclude_none=True).items():
        setattr(tipo, campo, valor)
    db.commit()
    db.refresh(tipo)
    return tipo


@router.delete("/{id_tipo}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_tipo(
    id_tipo: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(apenas_admin),
):
    tipo = db.query(Tipo).filter(Tipo.id_tipo == id_tipo).first()
    if not tipo:
        raise HTTPException(status_code=404, detail="Tipo não encontrado")
    db.delete(tipo)
    db.commit()
