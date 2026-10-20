from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import apenas_admin, get_usuario_atual
from app.database import get_db
from app.models.tipo_ocorrencia import TipoOcorrencia
from app.models.usuario import Usuario
from app.schemas.tipo_ocorrencia import TipoOcorrenciaCreate, TipoOcorrenciaOut, TipoOcorrenciaUpdate

router = APIRouter(prefix="/tipos", tags=["Tipos de Ocorrência"])


@router.get("/", response_model=List[TipoOcorrenciaOut])
def listar_tipos(
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_usuario_atual),
):
    return db.query(TipoOcorrencia).all()


@router.post("/", response_model=TipoOcorrenciaOut, status_code=status.HTTP_201_CREATED)
def criar_tipo(
    dados: TipoOcorrenciaCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(apenas_admin),
):
    tipo = TipoOcorrencia(**dados.model_dump())
    db.add(tipo)
    db.commit()
    db.refresh(tipo)
    return tipo


@router.put("/{tipo_id}", response_model=TipoOcorrenciaOut)
def atualizar_tipo(
    tipo_id: int,
    dados: TipoOcorrenciaUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(apenas_admin),
):
    tipo = db.query(TipoOcorrencia).filter(TipoOcorrencia.id == tipo_id).first()
    if not tipo:
        raise HTTPException(status_code=404, detail="Tipo não encontrado")
    for campo, valor in dados.model_dump(exclude_none=True).items():
        setattr(tipo, campo, valor)
    db.commit()
    db.refresh(tipo)
    return tipo


@router.delete("/{tipo_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_tipo(
    tipo_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(apenas_admin),
):
    tipo = db.query(TipoOcorrencia).filter(TipoOcorrencia.id == tipo_id).first()
    if not tipo:
        raise HTTPException(status_code=404, detail="Tipo não encontrado")
    db.delete(tipo)
    db.commit()
