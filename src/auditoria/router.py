from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.auditoria import service, schemas
from src.database import SessionLocal
from src.utilizadores.dependencies import get_current_user
from src.utilizadores.utils import is_master_admin

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=list[schemas.AuditoriaResponse])
def listar_auditoria(
    db: Session = Depends(get_db),
    utilizador_atual = Depends(get_current_user)
):
    if not is_master_admin(utilizador_atual):
        raise HTTPException(status_code=403, detail="Apenas o Master Admin pode consultar auditoria.")
    return service.listar_auditoria(db)