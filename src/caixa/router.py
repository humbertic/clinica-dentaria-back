from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any, Dict, List

from src.database import SessionLocal
from src.utilizadores.dependencies import get_current_user
from src.utilizadores.models import Utilizador
from src.utilizadores.utils import is_frontdesk

from src.caixa import service, schemas

router = APIRouter(prefix="/caixa/sessions", tags=["Caixa"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def frontoffice_only(user: Utilizador = Depends(get_current_user)):
    if not is_frontdesk(user): 
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a frontdesk"
        )
    return user

@router.get("", response_model=Dict[str, Any])
def get_open_session(db: Session = Depends(get_db)):
    sess = service.fetch_open_session(db)
    if not sess:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nenhuma sessão aberta")
    return sess

@router.post("", response_model=schemas.CaixaSessionRead, status_code=status.HTTP_201_CREATED)
def open_session(payload: schemas.CaixaSessionCreate,
                 db: Session = Depends(get_db),
                 user: Utilizador = Depends(frontoffice_only)):
    # Pass the authenticated user's ID to the service
    return service.open_session(db, payload, user.id)

@router.get("/{session_id}/pending")
def get_pending(session_id: int, db: Session = Depends(get_db),
                user: Utilizador = Depends(frontoffice_only)):
    return service.fetch_pending(db, session_id)

@router.post("/{session_id}/payments", response_model=schemas.CashierPaymentRead)
def pay(session_id: int,
        payload: schemas.CashierPaymentCreate,
        db: Session = Depends(get_db),
        user: Utilizador = Depends(frontoffice_only)):
    return service.register_payment(db, session_id, payload, user.id)

@router.post("/{session_id}/close", response_model=schemas.CaixaSessionRead)
def close(session_id: int,
          payload: schemas.CloseSessionRequest,
          db: Session = Depends(get_db),
          user: Utilizador = Depends(frontoffice_only)):
    return service.close_session(db, session_id, payload)
