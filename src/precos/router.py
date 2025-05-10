from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database import SessionLocal
from src.utilizadores.dependencies import get_current_user
from src.utilizadores.utils import is_master_admin
import src.precos.service as service
import src.precos.schemas as schemas

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.PrecoResponse, summary="Criar preço (Master Admin)")
def criar_preco(
    dados: schemas.PrecoCreate,
    db: Session = Depends(get_db),
    usuario = Depends(get_current_user)
):
    if not is_master_admin(usuario):
        raise HTTPException(403, "Apenas Master Admin pode criar preços.")
    return service.criar_preco(db, dados, criado_por=usuario.id)

@router.get("/", response_model=list[schemas.PrecoResponse], summary="Listar preços")
def listar_precos(
    db: Session = Depends(get_db),
    usuario = Depends(get_current_user)
):
    return service.listar_precos(db)

@router.get("/{artigo_id}/{entidade_id}", response_model=schemas.PrecoResponse, summary="Obter preço")
def obter_preco(
    artigo_id: int,
    entidade_id: int,
    db: Session = Depends(get_db),
    usuario = Depends(get_current_user)
):
    preco = service.obter_preco(db, artigo_id, entidade_id)
    if not preco:
        raise HTTPException(404, "Preço não encontrado.")
    return preco

@router.put("/{artigo_id}/{entidade_id}", response_model=schemas.PrecoResponse, summary="Atualizar preço (Master Admin)")
def atualizar_preco(
    artigo_id: int,
    entidade_id: int,
    dados: schemas.PrecoUpdate,
    db: Session = Depends(get_db),
    usuario = Depends(get_current_user)
):
    if not is_master_admin(usuario):
        raise HTTPException(403, "Apenas Master Admin pode atualizar preços.")
    preco = service.atualizar_preco(db, artigo_id, entidade_id, dados, atualizado_por=usuario.id)
    if not preco:
        raise HTTPException(404, "Preço não encontrado.")
    return preco

@router.delete("/{artigo_id}/{entidade_id}", response_model=dict, summary="Remover preço (Master Admin)")
def remover_preco(
    artigo_id: int,
    entidade_id: int,
    db: Session = Depends(get_db),
    usuario = Depends(get_current_user)
):
    if not is_master_admin(usuario):
        raise HTTPException(403, "Apenas Master Admin pode remover preços.")
    sucesso = service.remover_preco(db, artigo_id, entidade_id, removido_por=usuario.id)
    if not sucesso:
        raise HTTPException(404, "Preço não encontrado.")
    return {"detail": "Preço removido com sucesso."}