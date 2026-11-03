from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_usuario_atual
from app.database import get_db
from app.models.chamado import Chamado, StatusChamado
from app.models.cliente import Cliente
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

    abertos = sum(1 for c in todos if c.status in ["Chamados abertos", "aberto"])
    em_andamento = sum(1 for c in todos if c.status in ["Em andamento", "em_atendimento"])
    aguardando_retorno = sum(1 for c in todos if c.status == "Aguardando retorno")
    finalizados = sum(1 for c in todos if c.status in ["Finalizado", "finalizado"])

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
    id_tipo: Optional[int] = None,
    id_cliente: Optional[int] = None,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_usuario_atual),
):
    query = db.query(Chamado)
    if status_filtro:
        query = query.filter(Chamado.status == status_filtro)
    if id_tipo:
        query = query.filter(Chamado.id_tipo == id_tipo)
    if id_cliente:
        query = query.filter(Chamado.id_cliente == id_cliente)
    return query.all()


@router.post("/", response_model=ChamadoOut, status_code=status.HTTP_201_CREATED)
def criar_chamado(
    dados: ChamadoCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_usuario_atual),
):
    if not dados.id_cliente or not dados.id_tipo:
        raise HTTPException(
            status_code=400,
            detail="id_cliente e id_tipo são obrigatórios",
        )

    cliente = db.query(Cliente).filter(Cliente.id_cliente == dados.id_cliente).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    tipo = db.query(TipoOcorrencia).filter(TipoOcorrencia.id_tipo == dados.id_tipo).first()
    if not tipo:
        raise HTTPException(status_code=404, detail="Tipo de ocorrência não encontrado")

    payload = dados.model_dump(exclude={"cliente_id", "tipo_id"})
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

    payload = dados.model_dump(exclude_none=True, exclude={"tipo_id"})
    for campo, valor in payload.items():
        setattr(chamado, campo, valor)

    if dados.status in ["Finalizado", "finalizado"] and not chamado.data_fechamento:
        chamado.data_fechamento = datetime.utcnow()

    db.commit()
    db.refresh(chamado)
    return chamado
