from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date
from typing import List

from src.database import SessionLocal  
from src.utilizadores.dependencies import get_current_user  # Use this instead of direct import
from src.utilizadores.models import Utilizador

from src.relatorios.service import (
    get_cash_shift_range, get_revenue, get_top_services, get_cash_shifts,
    get_overdue_installments, get_stock_critical, get_productivity
)
from src.relatorios.schemas import (
    RevenueSummaryOut, TopServiceOut, CashShiftOut,
    OverdueInstallmentOut, StockCriticalOut, ProductivityClinicalOut
)

router = APIRouter(prefix="/reports", tags=["Relatórios"])

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ----------------------------------------------------------------------
@router.get("/revenue", response_model=List[RevenueSummaryOut])
def revenue(
    start: date,
    end: date,
    db: Session = Depends(get_db),
    current_user: Utilizador = Depends(get_current_user)
):
    # Optional: Check permissions
    # if not has_permission(current_user, "view_reports"):
    #     raise HTTPException(status_code=403, detail="Não tem permissão para aceder a relatórios")
    
    return get_revenue(db, start, end)

# ----------------------------------------------------------------------
@router.get("/top-services", response_model=List[TopServiceOut])
def top_services(
    limit: int = 5,
    db: Session = Depends(get_db),
    current_user: Utilizador = Depends(get_current_user)
):
    return get_top_services(db, limit)

# ----------------------------------------------------------------------
@router.get("/cash-shift", response_model=List[CashShiftOut])
def cash_shift(
    day: date,
    db: Session = Depends(get_db),
    current_user: Utilizador = Depends(get_current_user)
):
    return get_cash_shifts(db, day)

# ----------------------------------------------------------------------
@router.get("/overdue", response_model=List[OverdueInstallmentOut])
def overdue(
    max_age: int = 90,
    db: Session = Depends(get_db),
    current_user: Utilizador = Depends(get_current_user)
):
    return get_overdue_installments(db, max_age)

# ----------------------------------------------------------------------
@router.get("/stock-critical", response_model=List[StockCriticalOut])
def stock_critical(
    db: Session = Depends(get_db),
    current_user: Utilizador = Depends(get_current_user)
):
    return get_stock_critical(db)


@router.get("/cash-shift-range")
def cash_shift_range(
    start: date,
    end: date,
    db: Session = Depends(get_db),
    current_user: Utilizador = Depends(get_current_user)
):
    return get_cash_shift_range(db, start, end)


# ----------------------------------------------------------------------
@router.get("/productivity", response_model=List[ProductivityClinicalOut])
def productivity(
    month: date,
    db: Session = Depends(get_db),
    current_user: Utilizador = Depends(get_current_user)
):
    return get_productivity(db, month)

# ----------------------------------------------------------------------
# You have a duplicate endpoint - change the path to make it unique
@router.get("/revenue", response_model=List[RevenueSummaryOut])
def revenue(
    start: date,
    end: date,
    db: Session = Depends(get_db),
    current_user: Utilizador = Depends(get_current_user)
):
    # Check if user has access to this clinic
    # if not has_clinic_access(current_user, clinica_id):
    #     raise HTTPException(status_code=403, detail="Não tem acesso a esta clínica")
    
    return get_revenue(db, start, end)