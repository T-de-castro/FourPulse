from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_usuario_atual
from app.database import get_db
from app.models.chamado import Chamado, StatusChamado
from app.models.cliente import Cliente
from app.models.tipo import Tipo
from app.models.usuario import Usuario
from app.schemas.chamado import (
    ChamadoCreate,
    ChamadoOut,
    ChamadoUpdate,
    DashboardOut,
    normalizar_status,
)

router = APIRouter(prefix="/chamados", tags=["Chamados"])


@router.get("/dashboard", response_model=DashboardOut)
def dashboard(
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_usuario_atual),
):
    todos = db.query(Chamado).all()

    abertos = sum(1 for c in todos if c.status in [StatusChamado.ABERTO.value, "Chamados abertos", "aberto"])
    em_andamento = sum(1 for c in todos if c.status in [StatusChamado.EM_ANDAMENTO.value, "em_atendimento"])
    aguardando_retorno = sum(1 for c in todos if c.status == StatusChamado.AGUARDANDO_RETORNO.value)
    finalizados = sum(1 for c in todos if c.status in [StatusChamado.FINALIZADO.value, "finalizado"])

    por_tipo: dict[str, int] = {}
    for c in todos:
        nome_tipo = c.tipo.descricao if c.tipo else "Sem tipo"
        por_tipo[nome_tipo] = por_tipo.get(nome_tipo, 0) + 1

    return DashboardOut(
        abertos=abertos,
        em_andamento=em_andamento,
        aguardando_retorno=aguardando_retorno,
        finalizados=finalizados,
        total=len(todos),
        por_tipo=por_tipo,
    )


@router.get("/", response_model=List[ChamadoOut])
def listar_chamados(
    status_filtro: Optional[str] = None,
    tipo_id: Optional[int] = None,
    cliente_id: Optional[int] = None,
    id_tipo: Optional[int] = None,
    id_cliente: Optional[int] = None,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_usuario_atual),
):
    t_id = tipo_id or id_tipo
    c_id = cliente_id or id_cliente
    query = db.query(Chamado)
    if status_filtro:
        query = query.filter(Chamado.status == normalizar_status(status_filtro))
    if t_id:
        query = query.filter(Chamado.tipo_id == t_id)
    if c_id:
        query = query.filter(Chamado.cliente_id == c_id)
    return query.all()


@router.post("/", response_model=ChamadoOut, status_code=status.HTTP_201_CREATED)
def criar_chamado(
    dados: ChamadoCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_usuario_atual),
):
    if not dados.cliente_id or not dados.tipo_id:
        raise HTTPException(
            status_code=400,
            detail="cliente_id (ou id_cliente) e tipo_id (ou id_tipo) são obrigatórios",
        )

    cliente = db.query(Cliente).filter(Cliente.id_cliente == dados.cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    tipo = db.query(Tipo).filter(Tipo.id_tipo == dados.tipo_id).first()
    if not tipo:
        raise HTTPException(status_code=404, detail="Tipo não encontrado")

    payload = dados.model_dump(exclude={"id_cliente", "id_tipo"})
    chamado = Chamado(**payload)
    db.add(chamado)
    db.commit()
    db.refresh(chamado)
    return chamado


@router.get("/{id_chamado}", response_model=ChamadoOut)
def buscar_chamado(
    id_chamado: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_usuario_atual),
):
    chamado = db.query(Chamado).filter(Chamado.id_chamado == id_chamado).first()
    if not chamado:
        raise HTTPException(status_code=404, detail="Chamado não encontrado")
    return chamado


@router.put("/{id_chamado}", response_model=ChamadoOut)
def atualizar_chamado(
    id_chamado: int,
    dados: ChamadoUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_usuario_atual),
):
    chamado = db.query(Chamado).filter(Chamado.id_chamado == id_chamado).first()
    if not chamado:
        raise HTTPException(status_code=404, detail="Chamado não encontrado")

    payload = dados.model_dump(exclude_none=True, exclude={"id_tipo"})
    for campo, valor in payload.items():
        setattr(chamado, campo, valor)

    if chamado.status in [StatusChamado.FINALIZADO.value, "finalizado"] and not chamado.data_fechamento:
        chamado.data_fechamento = datetime.utcnow()

    db.commit()
    db.refresh(chamado)
    return chamado
