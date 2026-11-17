import os
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from fastapi import (
    APIRouter,
    Depends,
    File,
    Header,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy import case, func
from sqlalchemy.orm import Session, joinedload, selectinload

from app.auth.dependencies import (
    apenas_atendente_ou_admin,
    get_usuario_atual,
    get_usuario_ou_cliente,
)
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
    FinalizarChamadoRequest,
    normalizar_status,
)
from app.schemas.chamado_material import (
    ChamadoMaterialCreate,
    ChamadoMaterialOut,
    ChamadoMaterialUpdate,
)
from app.schemas.foto import ChamadoFotoOut
from app.utils.fotos import MAX_FOTOS_POR_CHAMADO, validar_conteudo_foto

UPLOAD_BASE_DIR = Path("uploads")

router = APIRouter(prefix="/chamados", tags=["Chamados"])

# Cache simples em memória para controle de idempotência (chave -> (timestamp, response_dict))
IDEMPOTENCY_CACHE: Dict[str, Tuple[float, dict]] = {}
IDEMPOTENCY_TTL_SECONDS = 600  # 10 minutos


def limpar_cache_idempotencia():
    agora = time.time()
    expirados = [
        k for k, (ts, _) in IDEMPOTENCY_CACHE.items() if agora - ts > IDEMPOTENCY_TTL_SECONDS
    ]
    for k in expirados:
        IDEMPOTENCY_CACHE.pop(k, None)


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
    skip: int = Query(0, ge=0),
    limit: Optional[int] = Query(50, ge=1, le=500),
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

    if skip:
        query = query.offset(skip)
    if limit is not None:
        query = query.limit(limit)
    return query.all()


@router.post("/", response_model=ChamadoOut, status_code=status.HTTP_201_CREATED)
def criar_chamado(
    dados: ChamadoCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(apenas_atendente_ou_admin),
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
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Tipo de chamado com ID {dados.tipo_id} não encontrado",
        )

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
    _: Usuario = Depends(apenas_atendente_ou_admin),
):
    chamado = db.query(Chamado).filter(Chamado.id_chamado == id_chamado).first()
    if not chamado:
        raise HTTPException(status_code=404, detail="Chamado não encontrado")

    if chamado.status in {StatusChamado.FINALIZADO.value, "finalizado"}:
        raise HTTPException(
            status_code=400,
            detail="Chamados finalizados não podem ser editados",
        )

    # Controle de concorrência otimista (Atividade D)
    if dados.versao is not None and dados.versao != chamado.versao:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Conflito de versão: o chamado foi alterado por outro usuário (versão atual: {chamado.versao}). Recarregue os dados e tente novamente.",
        )

    # Validação de tipo inexistente sem 500 (Atividade D)
    if dados.tipo_id is not None:
        tipo = db.query(Tipo).filter(Tipo.id_tipo == dados.tipo_id).first()
        if not tipo:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Tipo de chamado com ID {dados.tipo_id} não encontrado",
            )

    payload = dados.model_dump(exclude_none=True, exclude={"id_tipo", "versao"})
    for campo, valor in payload.items():
        setattr(chamado, campo, valor)

    chamado.versao = (chamado.versao or 1) + 1

    if chamado.status in [StatusChamado.FINALIZADO.value, "finalizado"] and not chamado.data_fechamento:
        chamado.data_fechamento = datetime.now(timezone.utc)

    db.commit()
    db.refresh(chamado)
    return chamado


# ==============================================================================
# SUB-RECURSO: FINALIZAÇÃO ATÔMICA / TRANSACIONAL
# ==============================================================================

@router.post("/{id_chamado}/finalizar", response_model=ChamadoOut)
def finalizar_chamado_transacional(
    id_chamado: int,
    dados: FinalizarChamadoRequest,
    db: Session = Depends(get_db),
    _: Usuario = Depends(apenas_atendente_ou_admin),
):
    """
    Encerra o chamado e vincula a lista de materiais em uma única transação atômica.
    Evita estados intermediários inconsistentes caso o envio de materiais falhe.
    """
    chamado = db.query(Chamado).filter(Chamado.id_chamado == id_chamado).first()
    if not chamado:
        raise HTTPException(status_code=404, detail="Chamado não encontrado")
    if chamado.status in [StatusChamado.FINALIZADO.value, "finalizado"]:
        raise HTTPException(status_code=400, detail="Chamado já está finalizado")

    try:
        # Se materiais foram enviados na finalização, processa-os atomicamente
        if dados.materiais:
            for item in dados.materiais:
                mat_id = item.material_id or item.id_material
                if not mat_id:
                    raise HTTPException(status_code=400, detail="material_id é obrigatório para cada material")
                mat = db.query(Material).filter(Material.id_material == mat_id).first()
                if not mat:
                    raise HTTPException(status_code=404, detail=f"Material {mat_id} não encontrado")

                vinculo = (
                    db.query(ChamadoMaterial)
                    .filter(
                        ChamadoMaterial.chamado_id == id_chamado,
                        ChamadoMaterial.material_id == mat_id,
                    )
                    .first()
                )
                if vinculo:
                    vinculo.quantidade += item.quantidade
                else:
                    vinculo = ChamadoMaterial(
                        chamado_id=id_chamado,
                        material_id=mat_id,
                        quantidade=item.quantidade,
                        valor_unitario=mat.valor or 0.00,
                    )
                    db.add(vinculo)

        chamado.status = StatusChamado.FINALIZADO.value
        chamado.data_fechamento = datetime.now(timezone.utc)
        chamado.versao = (chamado.versao or 1) + 1

        db.commit()
    except Exception as exc:
        db.rollback()
        if isinstance(exc, HTTPException):
            raise exc
        raise HTTPException(status_code=500, detail=f"Erro ao finalizar chamado: {str(exc)}")

    db.refresh(chamado)
    return chamado


# ==============================================================================
# SUB-RECURSO: CONTROLE DE MATERIAIS DO CHAMADO (COM HISTÓRICO E IDEMPOTÊNCIA)
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
    return (
        db.query(ChamadoMaterial)
        .options(joinedload(ChamadoMaterial.material))
        .filter(ChamadoMaterial.chamado_id == id_chamado)
        .all()
    )


@router.post(
    "/{id_chamado}/materiais",
    response_model=ChamadoMaterialOut,
    status_code=status.HTTP_201_CREATED,
)
def vincular_material_chamado(
    id_chamado: int,
    dados: ChamadoMaterialCreate,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    _: Usuario = Depends(apenas_atendente_ou_admin),
):
    limpar_cache_idempotencia()
    chave = idempotency_key or dados.idempotency_key
    if chave and chave in IDEMPOTENCY_CACHE:
        _, resposta_cache = IDEMPOTENCY_CACHE[chave]
        return resposta_cache

    chamado = db.query(Chamado).filter(Chamado.id_chamado == id_chamado).first()
    if not chamado:
        raise HTTPException(status_code=404, detail="Chamado não encontrado")

    # Bloqueio em chamado já finalizado (Atividade C)
    if chamado.status in [StatusChamado.FINALIZADO.value, "finalizado"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chamado já finalizado. Não é permitido adicionar ou alterar materiais após o encerramento.",
        )

    mat_id = dados.material_id or dados.id_material
    if not mat_id:
        raise HTTPException(status_code=400, detail="material_id é obrigatório")

    material = db.query(Material).filter(Material.id_material == mat_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material não encontrado")

    vinculo = (
        db.query(ChamadoMaterial)
        .filter(
            ChamadoMaterial.chamado_id == id_chamado,
            ChamadoMaterial.material_id == mat_id,
        )
        .first()
    )

    if vinculo:
        vinculo.quantidade += dados.quantidade
    else:
        # Grava preço histórico congelado no momento do uso (Atividade D)
        vinculo = ChamadoMaterial(
            chamado_id=id_chamado,
            material_id=mat_id,
            quantidade=dados.quantidade,
            valor_unitario=material.valor or 0.00,
        )
        db.add(vinculo)

    db.commit()
    db.refresh(vinculo)

    resultado = ChamadoMaterialOut.model_validate(vinculo)
    if chave:
        IDEMPOTENCY_CACHE[chave] = (time.time(), resultado.model_dump())
    return resultado


@router.post(
    "/{id_chamado}/materiais/lote",
    response_model=List[ChamadoMaterialOut],
    status_code=status.HTTP_201_CREATED,
)
def vincular_materiais_chamado(
    id_chamado: int,
    dados: List[ChamadoMaterialCreate],
    db: Session = Depends(get_db),
    _: Usuario = Depends(apenas_atendente_ou_admin),
):
    chamado = db.query(Chamado).filter(Chamado.id_chamado == id_chamado).first()
    if not chamado:
        raise HTTPException(status_code=404, detail="Chamado não encontrado")

    if chamado.status in [StatusChamado.FINALIZADO.value, "finalizado"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chamado já finalizado. Não é permitido adicionar materiais.",
        )

    if not dados:
        raise HTTPException(status_code=400, detail="Informe ao menos um material")

    quantidades = {}
    for item in dados:
        m_id = item.material_id or item.id_material
        if m_id is None:
            raise HTTPException(status_code=400, detail="material_id é obrigatório")
        quantidades[m_id] = quantidades.get(m_id, 0) + item.quantidade

    materials = db.query(Material).filter(Material.id_material.in_(quantidades)).all()
    materials_por_id = {m.id_material: m for m in materials}
    missing_ids = set(quantidades) - set(materials_por_id)
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
        mat = materials_por_id[material_id]
        if vinculo:
            vinculo.quantidade += quantidade
        else:
            vinculo = ChamadoMaterial(
                chamado_id=id_chamado,
                material_id=material_id,
                quantidade=quantidade,
                valor_unitario=mat.valor or 0.00,
            )
            db.add(vinculo)
        resultado.append(vinculo)

    db.commit()
    for item in resultado:
        db.refresh(item)
    return resultado


@router.put("/{id_chamado}/materiais/{id_material}", response_model=ChamadoMaterialOut)
def atualizar_quantidade_material_chamado(
    id_chamado: int,
    id_material: int,
    dados: ChamadoMaterialUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(apenas_atendente_ou_admin),
):
    chamado = db.query(Chamado).filter(Chamado.id_chamado == id_chamado).first()
    if not chamado:
        raise HTTPException(status_code=404, detail="Chamado não encontrado")

    if chamado.status in [StatusChamado.FINALIZADO.value, "finalizado"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chamado já finalizado. Não é permitido alterar materiais após o encerramento.",
        )

    vinculo = (
        db.query(ChamadoMaterial)
        .filter(
            ChamadoMaterial.chamado_id == id_chamado,
            ChamadoMaterial.material_id == id_material,
        )
        .first()
    )
    if not vinculo:
        raise HTTPException(status_code=404, detail="Material não vinculado a este chamado")

    vinculo.quantidade = dados.quantidade
    db.commit()
    db.refresh(vinculo)
    return vinculo


@router.delete("/{id_chamado}/materiais/{id_material}", status_code=status.HTTP_200_OK)
def remover_material_chamado(
    id_chamado: int,
    id_material: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(apenas_atendente_ou_admin),
):
    chamado = db.query(Chamado).filter(Chamado.id_chamado == id_chamado).first()
    if not chamado:
        raise HTTPException(status_code=404, detail="Chamado não encontrado")

    if chamado.status in [StatusChamado.FINALIZADO.value, "finalizado"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chamado já finalizado. Não é permitido remover materiais após o encerramento.",
        )

    vinculo = (
        db.query(ChamadoMaterial)
        .filter(
            ChamadoMaterial.chamado_id == id_chamado,
            ChamadoMaterial.material_id == id_material,
        )
        .first()
    )
    if not vinculo:
        raise HTTPException(status_code=404, detail="Material não vinculado a este chamado")

    db.delete(vinculo)
    db.commit()
    return {"status": "removido", "message": "Material desvinculado do chamado com sucesso."}


# ==============================================================================
# SUB-RECURSO: UPLOAD E DOWNLOAD PROTEGIDO DE FOTOS (COM VALIDAÇÃO DE CONTEÚDO)
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


@router.post(
    "/{id_chamado}/fotos",
    response_model=List[ChamadoFotoOut],
    status_code=status.HTTP_201_CREATED,
)
async def upload_fotos_chamado(
    id_chamado: int,
    fotos: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    _: Usuario = Depends(apenas_atendente_ou_admin),
):
    chamado = db.query(Chamado).filter(Chamado.id_chamado == id_chamado).first()
    if not chamado:
        raise HTTPException(status_code=404, detail="Chamado não encontrado")

    if not fotos:
        raise HTTPException(status_code=400, detail="Nenhum arquivo enviado")

    # Verifica limite total de fotos no chamado (Atividade B)
    total_existente = (
        db.query(func.count(ChamadoFoto.id_foto))
        .filter(ChamadoFoto.chamado_id == id_chamado)
        .scalar()
        or 0
    )
    if total_existente + len(fotos) > MAX_FOTOS_POR_CHAMADO:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Limite de {MAX_FOTOS_POR_CHAMADO} fotos por chamado excedido (já existem {total_existente} fotos).",
        )

    pasta_chamado = UPLOAD_BASE_DIR / "chamados" / str(id_chamado)
    pasta_chamado.mkdir(parents=True, exist_ok=True)

    arquivos_salvos: List[Tuple[Path, ChamadoFoto]] = []

    try:
        for file in fotos:
            nome_original = file.filename or "foto.jpg"
            conteudo = await file.read()

            # Validação rigorosa de magic bytes / extensão / tamanho (Atividade B)
            extensao_segura = validar_conteudo_foto(conteudo, nome_original)

            timestamp = int(datetime.now(timezone.utc).timestamp())
            uuid_sufixo = uuid.uuid4().hex[:6]
            nome_base = Path(sanitizar_nome_arquivo(nome_original)).stem
            nome_final = f"{timestamp}_{uuid_sufixo}_{nome_base}{extensao_segura}"

            caminho_completo = pasta_chamado / nome_final
            caminho_relativo = f"uploads/chamados/{id_chamado}/{nome_final}"

            # Grava no disco
            with open(caminho_completo, "wb") as buffer:
                buffer.write(conteudo)

            registro_foto = ChamadoFoto(
                chamado_id=id_chamado,
                caminho_foto=caminho_relativo,
            )
            db.add(registro_foto)
            arquivos_salvos.append((caminho_completo, registro_foto))

        db.commit()
    except Exception as exc:
        db.rollback()
        # Se houver qualquer falha no banco ou processamento, remove arquivos criados para evitar lixo órfão
        for caminho_arquivo, _ in arquivos_salvos:
            if caminho_arquivo.exists():
                try:
                    caminho_arquivo.unlink()
                except OSError:
                    pass
        if isinstance(exc, HTTPException):
            raise exc
        raise HTTPException(status_code=500, detail=f"Falha ao processar upload de fotos: {str(exc)}")

    for _, f in arquivos_salvos:
        db.refresh(f)

    return [f for _, f in arquivos_salvos]


@router.get("/{id_chamado}/fotos/{id_foto}/arquivo")
def download_foto_chamado(
    id_chamado: int,
    id_foto: int,
    db: Session = Depends(get_db),
    auth: dict = Depends(get_usuario_ou_cliente),
):
    """
    Download protegido de foto anexada ao chamado.
    Exige autenticação e aplica regras de autorização:
    - Usuário interno: acesso permitido se conta ativa.
    - Cliente externo: acesso permitido APENAS se o chamado pertencer a ele.
    """
    chamado = db.query(Chamado).filter(Chamado.id_chamado == id_chamado).first()
    if not chamado:
        raise HTTPException(status_code=404, detail="Chamado não encontrado")

    if auth.get("tipo") == "cliente":
        if chamado.cliente_id != auth.get("id_cliente"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado. Esta foto pertence ao chamado de outro cliente.",
            )

    foto = (
        db.query(ChamadoFoto)
        .filter(ChamadoFoto.id_foto == id_foto, ChamadoFoto.chamado_id == id_chamado)
        .first()
    )
    if not foto:
        raise HTTPException(status_code=404, detail="Foto não encontrada")

    arquivo_path = Path(foto.caminho_foto)
    if not arquivo_path.exists() or not arquivo_path.is_file():
        raise HTTPException(status_code=404, detail="Arquivo físico da foto não encontrado no servidor")

    ext = arquivo_path.suffix.lower()
    media_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }
    media_type = media_types.get(ext, "application/octet-stream")

    return FileResponse(
        path=arquivo_path,
        media_type=media_type,
        filename=arquivo_path.name,
        headers={"X-Content-Type-Options": "nosniff"},
    )


@router.delete("/{id_chamado}/fotos/{id_foto}", status_code=status.HTTP_200_OK)
def remover_foto_chamado(
    id_chamado: int,
    id_foto: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(apenas_atendente_ou_admin),
):
    foto = (
        db.query(ChamadoFoto)
        .filter(ChamadoFoto.id_foto == id_foto, ChamadoFoto.chamado_id == id_chamado)
        .first()
    )
    if not foto:
        raise HTTPException(status_code=404, detail="Foto não encontrada")

    caminho_arquivo = Path(foto.caminho_foto)
    if caminho_arquivo.exists() and caminho_arquivo.is_file():
        try:
            caminho_arquivo.unlink()
        except OSError:
            pass

    db.delete(foto)
    db.commit()
    return {"status": "removido", "message": "Foto removida com sucesso."}
