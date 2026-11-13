import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import case, func
from sqlalchemy.orm import Session, joinedload, selectinload

from app.auth.dependencies import get_usuario_atual
from app.database import get_db
from app.models.chamado import Chamado, StatusChamado
from app.models.cliente import Cliente
from app.models.foto import ChamadoFoto
from app.models.material import ChamadoMaterial, Material
from app.models.tipo import Tipo
from app.models.usuario import Usuario
from app.schemas.chamado import (
    ChamadoCreate,
    ChamadoOut,
    ChamadoUpdate,
    DashboardOut,
    normalizar_status,
)
from app.schemas.chamado_material import (
    ChamadoMaterialCreate,
    ChamadoMaterialOut,
    ChamadoMaterialUpdate,
)
from app.schemas.foto import ChamadoFotoOut

UPLOAD_BASE_DIR = Path("uploads")

router = APIRouter(prefix="/chamados", tags=["Chamados"])


@router.get("/dashboard", response_model=DashboardOut)
def dashboard(
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_usuario_atual),
):
    status_counts = dict(
        db.query(Chamado.status, func.count(Chamado.id_chamado))
        .group_by(Chamado.status)
        .all()
    )
    open_statuses = [StatusChamado.ABERTO.value, "Chamados abertos", "aberto"]
    type_counts = (
        db.query(
            Tipo.descricao,
            func.count(Chamado.id_chamado),
            func.sum(case((Chamado.status.in_(open_statuses), 1), else_=0)),
        )
        .outerjoin(Chamado, Chamado.tipo_id == Tipo.id_tipo)
        .group_by(Tipo.id_tipo, Tipo.descricao)
        .all()
    )
    por_tipo = {name: total for name, total, _ in type_counts}
    abertos_por_tipo = {name: opened or 0 for name, _, opened in type_counts}

    def count_status(*values):
        return sum(status_counts.get(value, 0) for value in values)

    return DashboardOut(
        abertos=count_status(*open_statuses),
        em_andamento=count_status(StatusChamado.EM_ANDAMENTO.value, "em_atendimento"),
        aguardando_retorno=count_status(StatusChamado.AGUARDANDO_RETORNO.value),
        finalizados=count_status(StatusChamado.FINALIZADO.value, "finalizado"),
        total=sum(status_counts.values()),
        por_tipo=por_tipo,
        abertos_por_tipo=abertos_por_tipo,
    )


@router.get("/", response_model=List[ChamadoOut])
def listar_chamados(
    status_filtro: Optional[str] = None,
    tipo_id: Optional[int] = None,
    cliente_id: Optional[int] = None,
    id_tipo: Optional[int] = None,
    id_cliente: Optional[int] = None,
    limit: Optional[int] = Query(None, ge=1, le=500),
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
    query = query.options(
        joinedload(Chamado.cliente),
        joinedload(Chamado.tipo),
        selectinload(Chamado.fotos),
        selectinload(Chamado.materiais).joinedload(ChamadoMaterial.material),
    ).order_by(Chamado.data_abertura.desc(), Chamado.id_chamado.desc())
    if limit is not None:
        query = query.limit(limit)
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
    chamado = (
        db.query(Chamado)
        .options(
            joinedload(Chamado.cliente),
            joinedload(Chamado.tipo),
            selectinload(Chamado.fotos),
            selectinload(Chamado.materiais).joinedload(ChamadoMaterial.material),
        )
        .filter(Chamado.id_chamado == id_chamado)
        .first()
    )
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
    if chamado.status in {StatusChamado.FINALIZADO.value, "finalizado"}:
        raise HTTPException(
            status_code=400,
            detail="Chamados finalizados não podem ser editados",
        )

    payload = dados.model_dump(exclude_none=True, exclude={"id_tipo"})
    for campo, valor in payload.items():
        setattr(chamado, campo, valor)

    if chamado.status in [StatusChamado.FINALIZADO.value, "finalizado"] and not chamado.data_fechamento:
        chamado.data_fechamento = datetime.now(timezone.utc)

    db.commit()
    db.refresh(chamado)
    return chamado


# ==============================================================================
# SUB-RECURSO: CONTROLE DE MATERIAIS DO CHAMADO
# ==============================================================================

@router.get("/{id_chamado}/materiais", response_model=List[ChamadoMaterialOut])
def listar_materiais_chamado(
    id_chamado: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_usuario_atual),
):
    chamado = db.query(Chamado).filter(Chamado.id_chamado == id_chamado).first()
    if not chamado:
        raise HTTPException(status_code=404, detail="Chamado não encontrado")
    return db.query(ChamadoMaterial).filter(ChamadoMaterial.chamado_id == id_chamado).all()


@router.post("/{id_chamado}/materiais", response_model=ChamadoMaterialOut, status_code=status.HTTP_201_CREATED)
def vincular_material_chamado(
    id_chamado: int,
    dados: ChamadoMaterialCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_usuario_atual),
):
    chamado = db.query(Chamado).filter(Chamado.id_chamado == id_chamado).first()
    if not chamado:
        raise HTTPException(status_code=404, detail="Chamado não encontrado")

    if not dados.material_id:
        raise HTTPException(status_code=400, detail="material_id é obrigatório")

    material = db.query(Material).filter(Material.id_material == dados.material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material não encontrado")

    # Verifica se o material já está vinculado ao chamado para atualizar quantidade
    vinculo = (
        db.query(ChamadoMaterial)
        .filter(
            ChamadoMaterial.chamado_id == id_chamado,
            ChamadoMaterial.material_id == dados.material_id,
        )
        .first()
    )

    if vinculo:
        vinculo.quantidade += dados.quantidade
    else:
        vinculo = ChamadoMaterial(
            chamado_id=id_chamado,
            material_id=dados.material_id,
            quantidade=dados.quantidade,
        )
        db.add(vinculo)

    db.commit()
    db.refresh(vinculo)
    return vinculo


@router.post(
    "/{id_chamado}/materiais/lote",
    response_model=List[ChamadoMaterialOut],
    status_code=status.HTTP_201_CREATED,
)
def vincular_materiais_chamado(
    id_chamado: int,
    dados: List[ChamadoMaterialCreate],
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_usuario_atual),
):
    chamado = db.query(Chamado).filter(Chamado.id_chamado == id_chamado).first()
    if not chamado:
        raise HTTPException(status_code=404, detail="Chamado não encontrado")
    if not dados:
        raise HTTPException(status_code=400, detail="Informe ao menos um material")

    quantidades = {}
    for item in dados:
        if item.material_id is None:
            raise HTTPException(status_code=400, detail="material_id é obrigatório")
        quantidades[item.material_id] = (
            quantidades.get(item.material_id, 0) + item.quantidade
        )

    materials = (
        db.query(Material)
        .filter(Material.id_material.in_(quantidades))
        .all()
    )
    material_ids = {material.id_material for material in materials}
    missing_ids = set(quantidades) - material_ids
    if missing_ids:
        raise HTTPException(
            status_code=404,
            detail=f"Material(is) não encontrado(s): {', '.join(map(str, sorted(missing_ids)))}",
        )

    vinculos = (
        db.query(ChamadoMaterial)
        .filter(
            ChamadoMaterial.chamado_id == id_chamado,
            ChamadoMaterial.material_id.in_(quantidades),
        )
        .all()
    )
    vinculos_por_material = {vinculo.material_id: vinculo for vinculo in vinculos}
    resultado = []
    for material_id, quantidade in quantidades.items():
        vinculo = vinculos_por_material.get(material_id)
        if vinculo:
            vinculo.quantidade += quantidade
        else:
            vinculo = ChamadoMaterial(
                chamado_id=id_chamado,
                material_id=material_id,
                quantidade=quantidade,
            )
            db.add(vinculo)
        resultado.append(vinculo)

    db.commit()
    for vinculo in resultado:
        db.refresh(vinculo)
    return resultado


@router.put("/{id_chamado}/materiais/{id_material}", response_model=ChamadoMaterialOut)
def atualizar_quantidade_material_chamado(
    id_chamado: int,
    id_material: int,
    dados: ChamadoMaterialUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_usuario_atual),
):
    vinculo = (
        db.query(ChamadoMaterial)
        .filter(
            ChamadoMaterial.chamado_id == id_chamado,
            ChamadoMaterial.material_id == id_material,
        )
        .first()
    )
    if not vinculo:
        raise HTTPException(
            status_code=404,
            detail="Material não vinculado a este chamado",
        )

    vinculo.quantidade = dados.quantidade
    db.commit()
    db.refresh(vinculo)
    return vinculo


@router.delete("/{id_chamado}/materiais/{id_material}", status_code=status.HTTP_200_OK)
def remover_material_chamado(
    id_chamado: int,
    id_material: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_usuario_atual),
):
    vinculo = (
        db.query(ChamadoMaterial)
        .filter(
            ChamadoMaterial.chamado_id == id_chamado,
            ChamadoMaterial.material_id == id_material,
        )
        .first()
    )
    if not vinculo:
        raise HTTPException(
            status_code=404,
            detail="Material não vinculado a este chamado",
        )

    db.delete(vinculo)
    db.commit()
    return {"status": "removido", "message": "Material desvinculado do chamado com sucesso."}


# ==============================================================================
# SUB-RECURSO: UPLOAD E GESTÃO DE FOTOS DO CHAMADO (ARMAZENAMENTO EM PASTAS)
# ==============================================================================

def sanitizar_nome_arquivo(nome: str) -> str:
    nome_limpo = re.sub(r"[^\w\.-]", "_", nome, flags=re.UNICODE)
    return nome_limpo or "foto.jpg"


@router.get("/{id_chamado}/fotos", response_model=List[ChamadoFotoOut])
def listar_fotos_chamado(
    id_chamado: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_usuario_atual),
):
    chamado = db.query(Chamado).filter(Chamado.id_chamado == id_chamado).first()
    if not chamado:
        raise HTTPException(status_code=404, detail="Chamado não encontrado")
    return db.query(ChamadoFoto).filter(ChamadoFoto.chamado_id == id_chamado).all()


@router.post("/{id_chamado}/fotos", response_model=List[ChamadoFotoOut], status_code=status.HTTP_201_CREATED)
async def upload_fotos_chamado(
    id_chamado: int,
    fotos: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_usuario_atual),
):
    chamado = db.query(Chamado).filter(Chamado.id_chamado == id_chamado).first()
    if not chamado:
        raise HTTPException(status_code=404, detail="Chamado não encontrado")

    if not fotos:
        raise HTTPException(status_code=400, detail="Nenhum arquivo enviado")

    # Diretório estruturado por chamado: uploads/chamados/{id_chamado}/
    pasta_chamado = UPLOAD_BASE_DIR / "chamados" / str(id_chamado)
    pasta_chamado.mkdir(parents=True, exist_ok=True)

    fotos_criadas: List[ChamadoFoto] = []

    for file in fotos:
        nome_original = file.filename or "foto.jpg"
        nome_seguro = sanitizar_nome_arquivo(nome_original)
        timestamp = int(datetime.now(timezone.utc).timestamp())
        uuid_sufixo = uuid.uuid4().hex[:6]
        nome_final = f"{timestamp}_{uuid_sufixo}_{nome_seguro}"

        caminho_completo = pasta_chamado / nome_final
        caminho_relativo = f"uploads/chamados/{id_chamado}/{nome_final}"

        # Grava arquivo no disco local
        with open(caminho_completo, "wb") as buffer:
            conteudo = await file.read()
            buffer.write(conteudo)

        # Registra foto no banco
        registro_foto = ChamadoFoto(
            chamado_id=id_chamado,
            caminho_foto=caminho_relativo,
        )
        db.add(registro_foto)
        fotos_criadas.append(registro_foto)

    db.commit()
    for f in fotos_criadas:
        db.refresh(f)

    return fotos_criadas


@router.delete("/{id_chamado}/fotos/{id_foto}", status_code=status.HTTP_200_OK)
def remover_foto_chamado(
    id_chamado: int,
    id_foto: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_usuario_atual),
):
    foto = (
        db.query(ChamadoFoto)
        .filter(ChamadoFoto.id_foto == id_foto, ChamadoFoto.chamado_id == id_chamado)
        .first()
    )
    if not foto:
        raise HTTPException(status_code=404, detail="Foto não encontrada")

    # Tenta remover o arquivo físico da pasta
    caminho_arquivo = Path(foto.caminho_foto)
    if caminho_arquivo.exists() and caminho_arquivo.is_file():
        try:
            caminho_arquivo.unlink()
        except OSError:
            pass

    db.delete(foto)
    db.commit()
    return {"status": "removido", "message": "Foto removida com sucesso."}
