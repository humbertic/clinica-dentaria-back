from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.database import SessionLocal
from src.utilizadores.dependencies import get_current_user
from src.utilizadores.models import Utilizador
from src.utilizadores.utils import is_master_admin

import src.artigos.service as service
import src.artigos.schemas as schemas

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.ArtigoResponse, summary="Criar novo artigo (Master Admin)")
def criar_artigo(
    dados: schemas.ArtigoCreate,
    db: Session = Depends(get_db),
    usuario: Utilizador = Depends(get_current_user)
):
    if not is_master_admin(usuario):
        raise HTTPException(403, "Apenas Master Admin pode criar artigos.")
    return service.criar_artigo(db, dados, criado_por_id=usuario.id)

@router.get("/", response_model=list[schemas.ArtigoResponse], summary="Listar artigos")
def listar_artigos(
    db: Session = Depends(get_db),
    usuario: Utilizador = Depends(get_current_user)
):
    return service.listar_artigos(db)

@router.get("/{artigo_id}", response_model=schemas.ArtigoResponse, summary="Obter artigo por ID")
def obter_artigo(
    artigo_id: int,
    db: Session = Depends(get_db),
    usuario: Utilizador = Depends(get_current_user)
):
    artigo = service.obter_artigo_por_id(db, artigo_id)
    if not artigo:
        raise HTTPException(404, "Artigo não encontrado.")
    return artigo

@router.put("/{artigo_id}", response_model=schemas.ArtigoResponse, summary="Atualizar artigo (Master Admin)")
def atualizar_artigo(
    artigo_id: int,
    dados: schemas.ArtigoUpdate,
    db: Session = Depends(get_db),
    usuario: Utilizador = Depends(get_current_user)
):
    if not is_master_admin(usuario):
        raise HTTPException(403, "Apenas Master Admin pode atualizar artigos.")
    artigo = service.atualizar_artigo(db, artigo_id, dados, atualizado_por_id=usuario.id)
    if not artigo:
        raise HTTPException(404, "Artigo não encontrado.")
    return artigo

@router.delete("/{artigo_id}", response_model=dict, summary="Remover artigo (Master Admin)")
def remover_artigo(
    artigo_id: int,
    db: Session = Depends(get_db),
    usuario: Utilizador = Depends(get_current_user)
):
    if not is_master_admin(usuario):
        raise HTTPException(403, "Apenas Master Admin pode remover artigos.")
    sucesso = service.remover_artigo(db, artigo_id, removido_por_id=usuario.id)
    if not sucesso:
        raise HTTPException(404, "Artigo não encontrado.")
    return {"detail": "Artigo removido com sucesso."}
