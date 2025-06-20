from datetime import datetime
from typing import Optional, List

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from src.caixa.models import CaixaSession, CashierPayment, CaixaStatus
from src.caixa.schemas import (
    CaixaSessionCreate, CloseSessionRequest, PendingInvoice, PendingParcela, CashierPaymentCreate
)
from src.faturacao.models import Fatura, ParcelaPagamento
from src.pacientes.models import Paciente

def fetch_open_session(db: Session) -> Optional[CaixaSession]:
    return db.query(CaixaSession)\
             .filter(CaixaSession.status == CaixaStatus.aberto)\
             .order_by(CaixaSession.data_inicio.desc())\
             .first()

def open_session(db: Session, payload: CaixaSessionCreate) -> CaixaSession:
    session = CaixaSession(**payload.dict())
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

def fetch_pending(db: Session, session_id: int) -> dict:
    # Todas as faturas não pagas
    invoices = (
        db.query(Fatura, Paciente.nome.label("paciente_nome"))
          .join(Paciente, Paciente.id == Fatura.paciente_id)
          .filter(Fatura.estado != "paga")
          .all()
    )
    pending_invoices = []
    for f, nome in invoices:
        pago = 0 if f.tipo == "consulta" and f.estado != "paga" else (
            sum(p.valor_pago or 0 for p in f.parcelas)
            if f.tipo == "plano" else f.total
        )
        pendente = float(f.total) - float(pago)
        pending_invoices.append(PendingInvoice(
            id=f.id,
            paciente_nome=nome,
            tipo=f.tipo.value,
            total=float(f.total),
            pendente=pendente,
            data_emissao=f.data_emissao
        ))
    # Todas as parcelas não pagas de planos
    parcelas = db.query(ParcelaPagamento)\
                 .filter(ParcelaPagamento.estado != "paga")\
                 .all()
    pending_parcelas = []
    for p in parcelas:
        pending_parcelas.append(PendingParcela(
            parcela_id=p.id,
            fatura_id=p.fatura_id,
            numero=p.numero,
            valor=float(p.valor_planejado),
            pendente=float(p.valor_planejado) - float(p.valor_pago or 0),
            data_vencimento=p.data_vencimento
        ))
    return {
        "invoices": pending_invoices,
        "parcelas": pending_parcelas
    }

def register_payment(
    db: Session,
    session_id: int,
    payload: CashierPaymentCreate,
    operador_id: int
) -> CashierPayment:
    # Validar sessão
    session = db.get(CaixaSession, session_id)
    if not session or session.status != CaixaStatus.aberto:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Sessão de caixa inválida ou fechada")
    # Criar pagamento
    pay = CashierPayment(
        session_id=session_id,
        operador_id=operador_id,
        **payload.dict(exclude_unset=True)
    )
    # Atualizar fatura/parcela
    if payload.parcela_id:
        from src.caixa.models import ParcelaPagamento as PP
        pp = db.get(PP, payload.parcela_id)
        pp.valor_pago = (pp.valor_pago or 0) + payload.valor_pago
        pp.data_pagamento = payload.data_pagamento or datetime.utcnow()
        pp.estado = "paga" if pp.valor_pago >= pp.valor_planejado else "parcial"
    elif payload.fatura_id:
        f = db.get(Fatura, payload.fatura_id)
        f.estado = "paga"
    else:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Deve indicar fatura_id ou parcela_id")
    db.add(pay)
    db.commit()
    db.refresh(pay)
    return pay

def close_session(db: Session, session_id: int, payload: CloseSessionRequest) -> CaixaSession:
    session = db.get(CaixaSession, session_id)
    if not session or session.status != CaixaStatus.aberto:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Sessão inválida ou já fechada")
    # Atualizar fecho
    session.valor_final = payload.valor_final
    session.data_fecho = datetime.utcnow()
    session.status = CaixaStatus.fechado
    db.commit()
    db.refresh(session)
    return session
