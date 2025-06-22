from datetime import datetime
from typing import Optional, List

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from src.comuns.enums import MetodoPagamento
from src.caixa.models import CaixaSession, CashierPayment, CaixaStatus
from src.caixa.schemas import (
    CaixaSessionCreate, CloseSessionRequest, PendingInvoice, PendingParcela, CashierPaymentCreate
)
from src.faturacao.models import Fatura, FaturaEstado, FaturaPagamento, FaturaTipo, ParcelaEstado, ParcelaPagamento
from src.pacientes.models import Paciente

def fetch_open_session(db: Session) -> Optional[dict]:
    """Fetch open session with detailed payment information and history."""
    session = db.query(CaixaSession)\
               .filter(CaixaSession.status == CaixaStatus.aberto)\
               .order_by(CaixaSession.data_inicio.desc())\
               .first()
    
    if not session:
        return None
    
    # Get all payments for this session
    payments = db.query(CashierPayment)\
                .filter(CashierPayment.session_id == session.id)\
                .order_by(CashierPayment.data_pagamento.desc())\
                .all()
    
    # Get customer names for each payment
    payment_details = []
    for payment in payments:
        customer_name = None
        
        # Get customer name if fatura_id is present
        if payment.fatura_id:
            fatura = db.query(Fatura).filter(Fatura.id == payment.fatura_id).first()
            if fatura and fatura.paciente_id:
                paciente = db.query(Paciente).filter(Paciente.id == fatura.paciente_id).first()
                if paciente:
                    customer_name = paciente.nome
        
        # Get customer name if parcela_id is present
        elif payment.parcela_id:
            parcela = db.query(ParcelaPagamento).filter(ParcelaPagamento.id == payment.parcela_id).first()
            if parcela and parcela.fatura_id:
                fatura = db.query(Fatura).filter(Fatura.id == parcela.fatura_id).first()
                if fatura and fatura.paciente_id:
                    paciente = db.query(Paciente).filter(Paciente.id == fatura.paciente_id).first()
                    if paciente:
                        customer_name = paciente.nome
        
        payment_details.append({
            "id": payment.id,
            "valor": float(payment.valor_pago),
            "metodo": payment.metodo_pagamento,
            "data": payment.data_pagamento,
            "paciente_nome": customer_name,
            "fatura_id": payment.fatura_id,
            "parcela_id": payment.parcela_id
        })
    
    # Calculate totals by payment method
    payment_totals = {}
    for payment in payments:
        method = payment.metodo_pagamento
        if method not in payment_totals:
            payment_totals[method] = {
                "count": 0,
                "total": 0
            }
        
        payment_totals[method]["count"] += 1
        payment_totals[method]["total"] += float(payment.valor_pago)
    
    # Calculate overall total
    total_amount = sum(float(p.valor_pago) for p in payments)
    
    # Return enriched session data
    return {
        "session": {
            "id": session.id,
            "data_inicio": session.data_inicio,
            "valor_inicial": float(session.valor_inicial),
            "status": session.status.value,
            "operador_id": session.operador_id,
            "operador_nome": session.operador.nome if session.operador else None
        },
        "payments": {
            "count": len(payments),
            "total": total_amount,
            "by_method": payment_totals,
            "history": payment_details
        }
    }
def open_session(db: Session, payload: CaixaSessionCreate, operador_id: int) -> CaixaSession:
    # Check if there's already an open session
    existing = fetch_open_session(db)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe uma sessão de caixa aberta"
        )
    
    # Create a new session with the authenticated user as the operator
    session_data = payload.dict()
    session_data["operador_id"] = operador_id  # Use the authenticated user's ID
    session_data["data_inicio"] = datetime.now()
    session_data["status"] = CaixaStatus.aberto
    
    session = CaixaSession(**session_data)
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
    pending_invoices: List[PendingInvoice] = []
    for f, nome in invoices:
        # Cálculo do valor pago
        if f.tipo.value == "consulta":
            pago = f.total if f.estado.name == "paga" else 0
        else:
            pago = sum(parc.valor_pago or 0 for parc in f.parcelas)
        pendente = float(f.total) - float(pago)
        pending_invoices.append(PendingInvoice(
            id=f.id,
            numero=str(f.id),
            data_emissao=f.data_emissao,
            paciente_nome=nome,
            total=float(f.total),
            pendente=pendente,
            tipo=f.tipo.value
        ))

    # Todas as parcelas não pagas de planos com nome do paciente
    rows = (
        db.query(ParcelaPagamento, Paciente.nome.label("paciente_nome"))  
          .join(Fatura, ParcelaPagamento.fatura_id == Fatura.id)
          .join(Paciente, Fatura.paciente_id == Paciente.id)
          .filter(ParcelaPagamento.estado != "paga")
          .all()
    )
    pending_parcelas: List[PendingParcela] = []
    for p, nome in rows:
        pend = float(p.valor_planejado) - float(p.valor_pago or 0)
        pending_parcelas.append(PendingParcela(
            parcela_id=p.id,
            fatura_id=p.fatura_id,
            numero=p.numero,
            valor=float(p.valor_planejado),
            pendente=pend,
            data_vencimento=p.data_vencimento,
            paciente_nome=nome  
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
    
    # Validate payment method
    try:
        metodo = MetodoPagamento(payload.metodo_pagamento)
    except ValueError:
        valid_methods = ", ".join([m.value for m in MetodoPagamento])
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, 
            f"Método de pagamento inválido. Métodos válidos: {valid_methods}"
        )
    
    # Begin transaction
    try:
        # Create cashier payment record
        payment = CashierPayment(
            session_id=session_id,
            operador_id=operador_id,
            fatura_id=payload.fatura_id,
            parcela_id=payload.parcela_id,
            valor_pago=payload.valor_pago,
            metodo_pagamento=metodo.value,
            data_pagamento=payload.data_pagamento or datetime.utcnow(),
            observacoes=payload.observacoes
        )
        
        # Handle parcela payment
        if payload.parcela_id:
            parcela = db.get(ParcelaPagamento, payload.parcela_id)
            if not parcela:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Parcela não encontrada")
                
            parcela.valor_pago = (parcela.valor_pago or 0) + payload.valor_pago
            parcela.data_pagamento = payload.data_pagamento or datetime.utcnow()
            parcela.estado = ParcelaEstado.paga if parcela.valor_pago >= parcela.valor_planejado else ParcelaEstado.parcial
            parcela.metodo_pagamento = metodo.value  # Sync payment method with cashier payment
            
            # Update parent invoice state if needed
            update_fatura_state(db, parcela.fatura_id)
            
        # Handle invoice payment
        elif payload.fatura_id:
            fatura = db.get(Fatura, payload.fatura_id)
            if not fatura:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Fatura não encontrada")
                
            # Create a FaturaPagamento record
            fatura_payment = FaturaPagamento(
                fatura_id=fatura.id,
                valor=payload.valor_pago,
                data_pagamento=payload.data_pagamento or datetime.utcnow(),
                metodo_pagamento=metodo.value,  # Sync payment method
                observacoes=payload.observacoes
            )
            db.add(fatura_payment)
            
            # Update invoice state
            total_paid = sum(p.valor for p in fatura.pagamentos) + payload.valor_pago
            if total_paid >= fatura.total:
                fatura.estado = FaturaEstado.paga
            else:
                fatura.estado = FaturaEstado.parcial
            
        else:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Deve indicar fatura_id ou parcela_id")
        
        db.add(payment)
        db.commit()
        db.refresh(payment)
        return payment
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Erro ao registrar pagamento: {str(e)}"
        )
    
def update_fatura_state(db: Session, fatura_id: int):
    """Update a fatura's state based on its parcelas' payment status"""
    fatura = db.get(Fatura, fatura_id)
    if not fatura:
        return
    
    # For plano faturas with parcelas
    if fatura.tipo == FaturaTipo.plano and fatura.parcelas:
        # Check if all parcelas are paid
        all_paid = all(p.estado == ParcelaEstado.paga for p in fatura.parcelas)
        some_paid = any(p.estado in [ParcelaEstado.paga, ParcelaEstado.parcial] for p in fatura.parcelas)
        
        if all_paid:
            fatura.estado = FaturaEstado.paga
        elif some_paid:
            fatura.estado = FaturaEstado.parcial
        else:
            fatura.estado = FaturaEstado.pendente
    
    db.commit()

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