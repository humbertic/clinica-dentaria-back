from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.perfis import service, schemas
from src.database import SessionLocal
from src.utilizadores.dependencies import get_current_user
from src.utilizadores import models as utilizador_models
from src.utilizadores.utils import is_master_admin  

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.PerfilResponse)
def criar_perfil(
    dados: schemas.PerfilCreate,
    db: Session = Depends(get_db),
    current_user: utilizador_models.Utilizador = Depends(get_current_user)
):
    if not is_master_admin(current_user):  # <-- Use the utility function
        raise HTTPException(status_code=403, detail="Apenas o Master Admin pode criar Perfis.")
    return service.criar_perfil(db, dados)

@router.put("/{perfil_id}", response_model=schemas.PerfilResponse)
def atualizar_perfil(
    perfil_id: int,
    dados: schemas.PerfilUpdate,
    db: Session = Depends(get_db),
    current_user: utilizador_models.Utilizador = Depends(get_current_user)
):
    if not is_master_admin(current_user):  # <-- Use the utility function
        raise HTTPException(status_code=403, detail="Apenas o Master Admin pode atualizar Perfis.")
    return service.atualizar_perfil(db, perfil_id, dados)

@router.get("/", response_model=list[schemas.PerfilResponse])
def listar_perfis(
    db: Session = Depends(get_db),
    current_user: utilizador_models.Utilizador = Depends(get_current_user)
):
    if not is_master_admin(current_user):  # <-- Use the utility function
        raise HTTPException(status_code=403, detail="Apenas o Master Admin pode listar Perfis.")
    return service.listar_perfis(db)


