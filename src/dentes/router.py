from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from src.database import SessionLocal
from src.dentes import schemas, service
from src.utilizadores.dependencies import get_current_user
from src.utilizadores.models import Utilizador


router = APIRouter()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=List[schemas.DenteResponse])
def listar_dentes(
    db: Session = Depends(get_db),
    utilizador_atual: Utilizador = Depends(get_current_user) 
    ):
    """Retorna todos os dentes cadastrados."""
    return service.listar_dentes(db)


@router.get("/faces", response_model=List[schemas.FaceResponse])
def listar_faces(db: Session = Depends(get_db),
    utilizador_atual: Utilizador = Depends(get_current_user)
    ):
    """Lista todas as faces dentárias."""
    return service.listar_faces(db)

@router.get("/tipo/{tipo}", response_model=List[schemas.DenteResponse])
def listar_por_tipo(
    tipo: str, db: Session = Depends(get_db),
    utilizador_atual: Utilizador = Depends(get_current_user)
    ):
    """Lista dentes por tipo (permanente/decíduo)."""
    return service.listar_dentes_por_tipo(db, tipo)


@router.get("/arcada/{arcada}", response_model=List[schemas.DenteResponse])
def listar_por_arcada(
    arcada: str, db: Session = Depends(get_db),
    utilizador_atual: Utilizador = Depends(get_current_user)
    ):
    """Lista dentes por arcada (superior/inferior)."""
    return service.listar_dentes_por_arcada(db, arcada)


@router.get("/{dente_id}", response_model=schemas.DenteResponse)
def obter_dente(
    dente_id: int, db: Session = Depends(get_db),
    utilizador_atual: Utilizador = Depends(get_current_user)
    ):
    """Busca um dente pelo ID."""
    dente = service.obter_dente_por_id(db, dente_id)
    if dente is None:
        raise HTTPException(status_code=404, detail="Dente não encontrado")
    return dente


