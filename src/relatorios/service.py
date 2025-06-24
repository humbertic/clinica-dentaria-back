from datetime import date
from typing import List
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from src.relatorios.models import (
    RevenueSummary, TopServices, CashShift,
    OverdueInstallment, StockCritical, ProductivityClinical
)
from src.relatorios.schemas import (
    RevenueSummaryOut, TopServiceOut, CashShiftOut,
    OverdueInstallmentOut, StockCriticalOut, ProductivityClinicalOut
)

# ----------------------------------------------------------------------
def rows_to_schema(db: Session, stmt, schema_cls):
    """Executa o SELECT e devolve lista de instâncias Pydantic."""
    return [schema_cls(**row) for row in db.execute(stmt).mappings().all()]

# ----------------------------------------------------------------------
def get_revenue(db: Session, start: date, end: date) -> List[RevenueSummaryOut]:
    tbl = RevenueSummary.__table__
    stmt = (
        select(tbl)
        .where(tbl.c.dia.between(start, end))
        .order_by(tbl.c.dia)
    )
    return rows_to_schema(db, stmt, RevenueSummaryOut)

# ----------------------------------------------------------------------
def get_top_services(db: Session, limit: int = 5) -> List[TopServiceOut]:
    tbl = TopServices.__table__
    stmt = select(tbl.c.servico, tbl.c.valor_total).limit(limit)
    return rows_to_schema(db, stmt, TopServiceOut)

# ----------------------------------------------------------------------
def get_cash_shifts(db: Session, day: date) -> List[CashShiftOut]:
    tbl = CashShift.__table__
    stmt = (
        select(tbl)
        .where(func.date(tbl.c.data_inicio) == day)
        .order_by(tbl.c.data_inicio)
    )
    return rows_to_schema(db, stmt, CashShiftOut)

# ----------------------------------------------------------------------
def get_overdue_installments(db: Session, max_age: int = 90) -> List[OverdueInstallmentOut]:
    tbl = OverdueInstallment.__table__
    stmt = (
        select(tbl)
        .where(tbl.c.dias_em_atraso <= max_age)
        .order_by(tbl.c.dias_em_atraso.desc())
    )
    return rows_to_schema(db, stmt, OverdueInstallmentOut)

# ----------------------------------------------------------------------
def get_stock_critical(db: Session) -> List[StockCriticalOut]:
    tbl = StockCritical.__table__
    stmt = select(tbl)
    return rows_to_schema(db, stmt, StockCriticalOut)

# ----------------------------------------------------------------------
def get_productivity(db: Session, month: date) -> List[ProductivityClinicalOut]:
    tbl = ProductivityClinical.__table__
    primeiro_dia = month.replace(day=1)
    stmt = (
        select(tbl)
        .where(func.date_trunc('month', tbl.c.mes) == primeiro_dia)
    )
    return rows_to_schema(db, stmt, ProductivityClinicalOut)


def get_cash_shift_range(db: Session, start: date, end: date):
    tbl = CashShift.__table__
    stmt = (
        select(
            func.date(tbl.c.data_inicio).label('dia'),
            func.sum(tbl.c.total_entradas).label('entradas')
        )
        .where(tbl.c.data_inicio.between(start, end))
        .group_by(func.date(tbl.c.data_inicio))
        .order_by(func.date(tbl.c.data_inicio))
    )
    return db.execute(stmt).mappings().all()
