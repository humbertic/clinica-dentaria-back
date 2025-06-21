from datetime import datetime
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from src.orcamento.models import EstadoOrc, Orcamento, OrcamentoItem
from src.faturacao.models import (
    Fatura,
    FaturaItem,
    FaturaPagamento,
    ParcelaPagamento,
    FaturaTipo,
    FaturaEstado,
    ParcelaEstado,
)
from src.caixa.models import CaixaSession, CashierPayment, CaixaStatus

from src.faturacao.schemas import (
    FaturaCreate,
    FaturaItemCreate,
    MetodoPagamento,
    ParcelaCreate,
)
from src.pacientes.models import Paciente, PlanoTratamento
from src.consultas.models import Consulta, ConsultaItem
from decimal import Decimal


def get_fatura(db: Session, fatura_id: int) -> Fatura:
    """
    Get a fatura with all related payment information using explicit joins
    """
    # Query with explicit eager loading of all payment-related relationships
    f = (db.query(Fatura)
         .options(
             joinedload(Fatura.pagamentos),
             joinedload(Fatura.parcelas),
             joinedload(Fatura.itens)
         )
         .filter(Fatura.id == fatura_id)
         .first())
    
    if not f:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            f"Fatura com ID={fatura_id} não encontrada"
        )
    
    return f


def list_faturas(
    db: Session,
    paciente_id: Optional[int] = None,
    tipo: Optional[FaturaTipo] = None,
    estado: Optional[FaturaEstado] = None,
) -> List[Fatura]:
    q = db.query(Fatura)
    if paciente_id is not None:
        q = q.filter(Fatura.paciente_id == paciente_id)
    if tipo is not None:
        q = q.filter(Fatura.tipo == tipo)
    if estado is not None:
        q = q.filter(Fatura.estado == estado)
    return q.order_by(Fatura.data_emissao.desc()).all()


def create_fatura(
    db: Session,
    payload: FaturaCreate
) -> Fatura:
    # 1) Validate paciente
    paciente = db.get(Paciente, payload.paciente_id)
    if not paciente:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Paciente não encontrado")

    # 2) Validate fields by type and get origin
    consulta = None
    plano = None
    
    if payload.tipo == FaturaTipo.consulta.value:
        # Consulta invoice: CONSULTA_ID required, PLANO_ID must be None
        if payload.consulta_id is None:
            raise HTTPException(400, "Deves enviar consulta_id para fatura de consulta")
        if payload.plano_id is not None:
            raise HTTPException(400, "Fatura de consulta não pode ter plano_id")
        
        consulta = db.get(Consulta, payload.consulta_id)
        if not consulta:
            raise HTTPException(404, "Consulta não encontrada")
            
        # Check if invoice already exists for this consulta
        existing = db.query(Fatura).filter(
            Fatura.consulta_id == payload.consulta_id,
            Fatura.tipo == FaturaTipo.consulta
        ).first()
        
        if existing:
            # A consulta can only have one invoice, so return it regardless of status
            return existing
            
    elif payload.tipo == FaturaTipo.plano.value:
        # Plano invoice: PLANO_ID required, CONSULTA_ID must be None
        if payload.plano_id is None:
            raise HTTPException(400, "Deves enviar plano_id para fatura de plano")
        if payload.consulta_id is not None:
            raise HTTPException(400, "Fatura de plano não pode ter consulta_id")
        
        plano = db.get(PlanoTratamento, payload.plano_id)
        if not plano:
            raise HTTPException(404, "Plano de tratamento não encontrado")
        
        # Check for existing invoice for this plano, but only return if not canceled
        existing = db.query(Fatura).filter(
            Fatura.plano_id == payload.plano_id,
            Fatura.tipo == FaturaTipo.plano,
            Fatura.estado != FaturaEstado.cancelada  # Don't consider canceled invoices
        ).first()
        
        if existing:
            # Return existing invoice only if it's not canceled
            # This allows creating a new invoice if the old one was canceled
            return existing
    else:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, 
            f"Tipo de fatura inválido: {payload.tipo}"
        )
 
    # 3) Create initial invoice
    fatura = Fatura(
        paciente_id = payload.paciente_id,
        tipo        = payload.tipo,
        consulta_id = payload.consulta_id,
        plano_id    = payload.plano_id,
        total       = 0,
        estado      = FaturaEstado.pendente,
    )
    db.add(fatura)
    db.commit()
    db.refresh(fatura)

    # 4) Generate items automatically
    total = 0

    if payload.tipo == FaturaTipo.consulta.value:
        # For consulta invoices, get items from the consulta
        itens = (
            db.query(ConsultaItem)
            .filter(ConsultaItem.consulta_id == payload.consulta_id)
            .all()
        )
        
        for ci in itens:
            descricao = ci.artigo.descricao if ci.artigo else f"Procedimento #{ci.id}"
            fi = FaturaItem(
                fatura_id      = fatura.id,
                origem_tipo    = "consulta_item",
                origem_id      = ci.id,
                quantidade     = ci.quantidade,
                preco_unitario = float(ci.preco_unitario),
                total          = float(ci.total),
                descricao      = descricao
            )
            db.add(fi)
            total += float(ci.total)

    elif payload.tipo == FaturaTipo.plano.value:
        # For plano invoices, get items from the plano
        # First check for an approved budget for this patient
        orc = (
            db.query(Orcamento)
            .filter(Orcamento.paciente_id == payload.paciente_id)
            .filter(Orcamento.estado == EstadoOrc.aprovado)
            .order_by(Orcamento.data.desc())
            .first()
        )
        
        if not orc:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                "Não existe orçamento aprovado para este paciente"
            )

        # Generate items from the plano
        total = 0
        for pi in plano.itens:
            # Get price and quantity from the approved budget
            oi = db.get(OrcamentoItem, pi.orcamento_item_id)
            if not oi:
                continue  # Skip items without an associated budget
                
            descricao = None
            if oi.artigo:
                descricao = oi.artigo.descricao
            else:
                descricao = f"Procedimento #{pi.id}"

            valor_unit = float(oi.preco_paciente)
            qtd = pi.quantidade_prevista
            fi = FaturaItem(
                fatura_id      = fatura.id,
                origem_tipo    = "plano_item",
                origem_id      = pi.id,
                quantidade     = qtd,
                preco_unitario = valor_unit,
                total          = qtd * valor_unit,
                descricao      = descricao
            )
            db.add(fi)
            total += qtd * valor_unit

    # 5) Update invoice total
    fatura.total = total
    db.commit()
    db.refresh(fatura)
    return fatura


def add_item(
    db: Session,
    fatura_id: int,
    payload: FaturaItemCreate
) -> FaturaItem:
    fatura = get_fatura(db, fatura_id)

    # 1) validar origem
    if payload.origem_tipo == "consulta_item":
        # só em faturas de consulta
        if fatura.tipo != FaturaTipo.consulta:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "Só pode adicionar itens de consulta a faturas de consulta"
            )
        # não validamos aqui a existência do ConsultaItem (assumimos que já exista)
    elif payload.origem_tipo == "plano_item":
        if fatura.tipo != FaturaTipo.plano:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "Só pode adicionar itens de plano a faturas de plano"
            )
    else:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "origem_tipo inválido (deve ser 'consulta_item' ou 'plano_item')"
        )

    # 2) criar item e atualizar total da fatura
    total_item = payload.quantidade * payload.preco_unitario
    item = FaturaItem(
        fatura_id      = fatura.id,
        origem_tipo    = payload.origem_tipo,
        origem_id      = payload.origem_id,
        quantidade     = payload.quantidade,
        preco_unitario = payload.preco_unitario,
        total          = total_item,
    )
    db.add(item)

    # 3) atualizar total e persistir
    fatura.total += total_item
    db.commit()
    db.refresh(item)
    db.refresh(fatura)
    return item


def generate_parcelas(
    db: Session,
    fatura_id: int,
    parcel_defs: List[ParcelaCreate]
) -> List[ParcelaPagamento]:
    fatura = get_fatura(db, fatura_id)

    if fatura.tipo != FaturaTipo.plano:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Só faturas de plano podem ter parcelas"
        )

    if fatura.parcelas:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Parcelas já foram definidas para esta fatura"
        )

    # verificar soma dos valores
    soma = sum(p.valor_planejado for p in parcel_defs)
    if float(soma) != float(fatura.total):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Soma das parcelas não coincide com total da fatura"
        )

    created = []
    for pdef in parcel_defs:
        parc = ParcelaPagamento(
            fatura_id       = fatura.id,
            numero          = pdef.numero,
            valor_planejado = pdef.valor_planejado,
            data_vencimento = pdef.data_vencimento,
            estado          = ParcelaEstado.pendente,
        )
        db.add(parc)
        created.append(parc)

    db.commit()
    # atualizar instância de fatura
    db.refresh(fatura)
    return fatura.parcelas


def pay_parcela(
    db: Session,
    parcela_id: int,
    valor_pago: float,
    metodo_pagamento: str,
    data_pagamento: Optional[datetime] = None,
    observacoes: Optional[str] = None,
    session_id: Optional[int] = None,  
    operador_id: Optional[int] = None  
) -> ParcelaPagamento:
    parc = db.get(ParcelaPagamento, parcela_id)
    if not parc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            f"Parcela com ID={parcela_id} não encontrada"
        )

    # 1) atualizar valor pago, método e data
    effective_date = data_pagamento or datetime.utcnow()
    parc.valor_pago = valor_pago
    parc.data_pagamento = effective_date
    parc.metodo_pagamento = metodo_pagamento
    
    # 2) determinar estado da parcela
    if valor_pago >= float(parc.valor_planejado):
        parc.estado = ParcelaEstado.paga
    elif valor_pago > 0:
        parc.estado = ParcelaEstado.parcial
    else:
        parc.estado = ParcelaEstado.pendente

    # 3) atualizar estado da fatura
    fatura = parc.fatura
    soma_pago = sum(Decimal(p.valor_pago or 0) for p in fatura.parcelas)

    if soma_pago >= float(fatura.total):
        fatura.estado = FaturaEstado.paga
    elif soma_pago > 0:
        fatura.estado = FaturaEstado.parcial
    else:
        fatura.estado = FaturaEstado.pendente

    # 4) Register in caixa if session_id is provided
    if session_id and operador_id:
        
        # Verify if session exists and is open
        session = db.get(CaixaSession, session_id)
        if not session or session.status != CaixaStatus.aberto:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, 
                "Sessão de caixa inválida ou fechada"
            )
            
        # Create cashier payment record
        payment = CashierPayment(
            session_id=session_id,
            operador_id=operador_id,
            parcela_id=parcela_id,
            valor_pago=valor_pago,
            metodo_pagamento=metodo_pagamento,
            data_pagamento=effective_date,
            observacoes=observacoes
        )
        db.add(payment)

    db.commit()
    db.refresh(parc)
    return parc


def pay_fatura_direto(
    db: Session,
    fatura_id: int,
    valor_pago: float,
    metodo_pagamento: MetodoPagamento,
    data_pagamento: Optional[datetime] = None,
    observacoes: Optional[str] = None,
    session_id: Optional[int] = None,  
    operador_id: Optional[int] = None  
) -> Fatura:
    """
    Process a direct payment to an invoice without going through parcelas.
    
    For invoices without installment plans, this creates a single payment
    directly against the invoice.
    """
    # 1) Get the invoice
    fatura = get_fatura(db, fatura_id)
    if not fatura:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            f"Fatura com ID={fatura_id} não encontrada"
        )
    
    # 2) Check if invoice can receive payments
    if fatura.estado == FaturaEstado.cancelada:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Não é possível pagar uma fatura cancelada"
        )
    
    if fatura.estado == FaturaEstado.paga:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Esta fatura já está totalmente paga"
        )
    
    # 3) For invoice with parcelas, redirect to parcela payment
    if fatura.parcelas:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Esta fatura tem parcelas definidas. Faça o pagamento através de uma parcela específica."
        )
    
    # 4) Set payment date if not provided
    effective_date = data_pagamento or datetime.utcnow()
    
    # 5) Create a payment record 
    pagamento = FaturaPagamento(
        fatura_id=fatura_id,
        valor=valor_pago,
        data_pagamento=effective_date,
        metodo_pagamento=metodo_pagamento.value,  # Use .value to get the string
        observacoes=observacoes
    )
    db.add(pagamento)
    
    # 6) Update invoice status based on the payment
    total_pago = db.query(func.sum(FaturaPagamento.valor)).filter(
        FaturaPagamento.fatura_id == fatura_id
    ).scalar() or 0
    total_pago += valor_pago  
    
    if total_pago >= float(fatura.total):
        fatura.estado = FaturaEstado.paga
    elif total_pago > 0:
        fatura.estado = FaturaEstado.parcial
    
    # 7) Register in caixa if session_id is provided
    if session_id and operador_id:
        from src.caixa.models import CaixaSession, CashierPayment, CaixaStatus
        
        # Verify if session exists and is open
        session = db.get(CaixaSession, session_id)
        if not session or session.status != CaixaStatus.aberto:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, 
                "Sessão de caixa inválida ou fechada"
            )
            
        # Create cashier payment record
        payment = CashierPayment(
            session_id=session_id,
            operador_id=operador_id,
            fatura_id=fatura_id,
            valor_pago=valor_pago,
            metodo_pagamento=metodo_pagamento.value,  # Use .value to get the string
            data_pagamento=effective_date,
            observacoes=observacoes
        )
        db.add(payment)
    
    db.commit()
    db.refresh(fatura)
    return fatura