from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database import SessionLocal
from src.utilizadores.dependencies import get_current_user
from src.utilizadores.models import Utilizador
from src.utilizadores.utils import is_master_admin
from . import service, schemas

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("", response_model=list[schemas.EntidadeResponse])
def listar_entidades(
    db: Session = Depends(get_db),
    user: Utilizador = Depends(get_current_user)
):
    return service.listar_entidades(db)

@router.get("/{entidade_id}", response_model=schemas.EntidadeResponse)
def obter_entidade(
    entidade_id: int,
    db: Session = Depends(get_db),
    user: Utilizador = Depends(get_current_user)
):
    ent = service.obter_entidade_por_id(db, entidade_id)
    if not ent:
        raise HTTPException(status_code=404, detail="Entidade não encontrada.")
    return ent

@router.post("", response_model=schemas.EntidadeResponse)
def criar_entidade(
    dados: schemas.EntidadeCreate,
    db: Session = Depends(get_db),
    user: Utilizador = Depends(get_current_user)
):
    if not is_master_admin(user):
        raise HTTPException(status_code=403, detail="Apenas Master Admin pode criar entidade.")
    return service.criar_entidade(db, dados, user)

@router.put("/{entidade_id}", response_model=schemas.EntidadeResponse)
def atualizar_entidade(
    entidade_id: int,
    dados: schemas.EntidadeUpdate,
    db: Session = Depends(get_db),
    user: Utilizador = Depends(get_current_user)
):
    if not is_master_admin(user):
        raise HTTPException(status_code=403, detail="Apenas Master Admin pode atualizar entidade.")
    ent = service.atualizar_entidade(db, entidade_id, dados, user)
    if not ent:
        raise HTTPException(status_code=404, detail="Entidade não encontrada.")
    return ent

@router.delete("/{entidade_id}", response_model=dict)
def remover_entidade(
    entidade_id: int,
    db: Session = Depends(get_db),
    user: Utilizador = Depends(get_current_user)
):
    if not is_master_admin(user):
        raise HTTPException(status_code=403, detail="Apenas Master Admin pode remover entidade.")
    ent = service.remover_entidade(db, entidade_id, user)
    if not ent:
        raise HTTPException(status_code=404, detail="Entidade não encontrada.")
    return {"detail": "Entidade removida com sucesso."}
