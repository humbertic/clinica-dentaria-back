from typing import Optional, List

from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import EmailStr
from sqlalchemy.orm import Session

from src.database import SessionLocal
from src.utilizadores.dependencies import get_current_user
from src.utilizadores.models import Utilizador
from src.email.service import EmailManager
from src.email.util import get_email_config, test_email_config
from src.marcacoes.service import get_marcacao as obter_marcacao   # função helper no seu módulo

router = APIRouter(prefix="/email", tags=["Email"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------- Teste de configuração ----------------------------------------
@router.post("/test")
async def testar_email(
    clinica_id: int = Query(..., description="ID da clínica"),
    db: Session = Depends(get_db),
    current_user: Utilizador = Depends(get_current_user),
):
    config = await get_email_config(clinica_id, db)
    await test_email_config(config)
    return {"detail": "Configuração OK"}

# ---------- Fatura --------------------------------------------------------
@router.post("/fatura/{fatura_id}")
async def enviar_fatura_email(
    fatura_id: int,
    clinica_id: int = Query(...),
    email_para: Optional[EmailStr] = None,
    db: Session = Depends(get_db),
    current_user: Utilizador = Depends(get_current_user),
):
    config = await get_email_config(clinica_id, db)
    svc = EmailManager(db, config)
    await svc.enviar_fatura(fatura_id, clinica_id, email_para)
    return {"detail": "Fatura enviada"}

# ---------- Orçamento -----------------------------------------------------
@router.post("/orcamento/{orcamento_id}")
async def enviar_orcamento_email(
    orcamento_id: int,
    clinica_id: int = Query(...),
    email_para: Optional[EmailStr] = None,
    db: Session = Depends(get_db),
    current_user: Utilizador = Depends(get_current_user),
):
    config = await get_email_config(clinica_id, db)
    svc = EmailManager(db, config)
    await svc.enviar_orcamento(orcamento_id, clinica_id, email_para)
    return {"detail": "Orçamento enviado"}

# ---------- Lembrete de consulta -----------------------------------------
@router.post("/marcacoes/{marc_id}/lembrete", status_code=status.HTTP_202_ACCEPTED)
async def enviar_lembrete_email(
    marc_id: int,
    db: Session = Depends(get_db),
    current_user: Utilizador = Depends(get_current_user),
):
    marc = obter_marcacao(db, marc_id)
    config = await get_email_config(marc.clinic_id, db)
    svc = EmailManager(db, config)
    await svc.enviar_lembrete(marc)
    return {"detail": "Lembrete enviado"}

# ---------- Cancelamento de consulta -------------------------------------
@router.post("/marcacoes/{marc_id}/cancelamento", status_code=status.HTTP_202_ACCEPTED)
async def enviar_cancelamento_email(
    marc_id: int,
    db: Session = Depends(get_db),
    current_user: Utilizador = Depends(get_current_user),
):
    marc = obter_marcacao(db, marc_id)
    if marc.estado != "cancelada":
        raise HTTPException(400, "Marcação não está cancelada")

    config = await get_email_config(marc.clinic_id, db)
    svc = EmailManager(db, config)
    await svc.enviar_cancelamento(marc)
    return {"detail": "Cancelamento enviado"}
