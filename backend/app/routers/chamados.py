from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_usuario_atual
from app.database import get_db
from app.models.chamado import Chamado, StatusChamado
from app.models.tipo_ocorrencia import TipoOcorrencia
from app.models.usuario import Usuario
from app.schemas.chamado import ChamadoCreate, ChamadoOut, ChamadoUpdate, DashboardOut

router = APIRouter(prefix="/chamados", tags=["Chamados"])


@router.get("/dashboard", response_model=DashboardOut)
def dashboard(
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_usuario_atual),
):
    todos = db.query(Chamado).all()

    abertos = sum(1 for c in todos if c.status == StatusChamado.aberto)
    em_atendimento = sum(1 for c in todos if c.status == StatusChamado.em_atendimento)
    finalizados = sum(1 for c in todos if c.status == StatusChamado.finalizado)

    por_tipo: dict[str, int] = {}
    for c in todos:
        nome_tipo = c.tipo.descricao if c.tipo else "Sem tipo"
        por_tipo[nome_tipo] = por_tipo.get(nome_tipo, 0) + 1

    por_prioridade: dict[str, int] = {}
    for c in todos:
        prio = c.prioridade.value if c.prioridade else "sem_prioridade"
        por_prioridade[prio] = por_prioridade.get(prio, 0) + 1

    return DashboardOut(
        abertos=abertos,
        em_atendimento=em_atendimento,
        finalizados=finalizados,
        por_tipo=por_tipo,
        por_prioridade=por_prioridade,
    )


@router.get("/", response_model=List[ChamadoOut])
def listar_chamados(
    status_filtro: Optional[StatusChamado] = None,
    tipo_id: Optional[int] = None,
    responsavel_id: Optional[int] = None,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_usuario_atual),
):
    query = db.query(Chamado)
    if status_filtro:
        query = query.filter(Chamado.status == status_filtro)
    if tipo_id:
        query = query.filter(Chamado.tipo_id == tipo_id)
    if responsavel_id:
        query = query.filter(Chamado.responsavel_id == responsavel_id)
    return query.all()


@router.post("/", response_model=ChamadoOut, status_code=status.HTTP_201_CREATED)
def criar_chamado(
    dados: ChamadoCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_usuario_atual),
):
    chamado = Chamado(**dados.model_dump())
    db.add(chamado)
    db.commit()
    db.refresh(chamado)
    return chamado


@router.get("/{chamado_id}", response_model=ChamadoOut)
def buscar_chamado(
    chamado_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_usuario_atual),
):
    chamado = db.query(Chamado).filter(Chamado.id == chamado_id).first()
    if not chamado:
        raise HTTPException(status_code=404, detail="Chamado não encontrado")
    return chamado


@router.put("/{chamado_id}", response_model=ChamadoOut)
def atualizar_chamado(
    chamado_id: int,
    dados: ChamadoUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_usuario_atual),
):
    chamado = db.query(Chamado).filter(Chamado.id == chamado_id).first()
    if not chamado:
        raise HTTPException(status_code=404, detail="Chamado não encontrado")
    for campo, valor in dados.model_dump(exclude_none=True).items():
        setattr(chamado, campo, valor)
    db.commit()
    db.refresh(chamado)
    return chamado
