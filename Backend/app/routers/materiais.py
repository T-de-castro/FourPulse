from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_usuario_atual
from app.database import get_db
from app.models.material import ChamadoMaterial, Material
from app.models.usuario import Usuario
from app.schemas.material import MaterialCreate, MaterialOut, MaterialUpdate

router = APIRouter(prefix="/materiais", tags=["Materiais"])


@router.get("/", response_model=List[MaterialOut])
def listar_materiais(
    apenas_ativos: bool = Query(True, description="Filtrar apenas materiais com status ativo"),
    busca: Optional[str] = Query(None, description="Buscar por descrição ou unidade"),
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_usuario_atual),
):
    query = db.query(Material)
    if apenas_ativos:
        query = query.filter(Material.status.is_(True))
    if busca:
        termo = f"%{busca.strip()}%"
        query = query.filter(
            (Material.descricao.ilike(termo)) | (Material.unidade_medida.ilike(termo))
        )
    return query.order_by(Material.descricao.asc()).all()


@router.post("/", response_model=MaterialOut, status_code=status.HTTP_201_CREATED)
def criar_material(
    dados: MaterialCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_usuario_atual),
):
    material_existente = (
        db.query(Material)
        .filter(Material.descricao.ilike(dados.descricao.strip()))
        .first()
    )
    if material_existente:
        raise HTTPException(
            status_code=400,
            detail=f"Material com a descrição '{dados.descricao}' já existe.",
        )

    novo_material = Material(
        descricao=dados.descricao.strip(),
        unidade_medida=dados.unidade_medida.strip().upper(),
        status=dados.status,
    )
    db.add(novo_material)
    db.commit()
    db.refresh(novo_material)
    return novo_material


@router.get("/{id_material}", response_model=MaterialOut)
def buscar_material(
    id_material: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_usuario_atual),
):
    material = db.query(Material).filter(Material.id_material == id_material).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material não encontrado.")
    return material


@router.put("/{id_material}", response_model=MaterialOut)
def atualizar_material(
    id_material: int,
    dados: MaterialUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_usuario_atual),
):
    material = db.query(Material).filter(Material.id_material == id_material).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material não encontrado.")

    payload = dados.model_dump(exclude_none=True)
    if "descricao" in payload:
        payload["descricao"] = payload["descricao"].strip()
    if "unidade_medida" in payload:
        payload["unidade_medida"] = payload["unidade_medida"].strip().upper()

    for campo, valor in payload.items():
        setattr(material, campo, valor)

    db.commit()
    db.refresh(material)
    return material


@router.delete("/{id_material}", status_code=status.HTTP_200_OK)
def remover_material(
    id_material: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_usuario_atual),
):
    material = db.query(Material).filter(Material.id_material == id_material).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material não encontrado.")

    # Se estiver vinculado a algum chamado, inativa em vez de deletar fisicamente
    vinculos = db.query(ChamadoMaterial).filter(ChamadoMaterial.material_id == id_material).first()
    if vinculos:
        material.status = False
        db.commit()
        return {
            "status": "inativado",
            "message": "Material inativado com sucesso (possui vínculos com chamados).",
        }

    db.delete(material)
    db.commit()
    return {"status": "removido", "message": "Material removido com sucesso."}
