from datetime import datetime
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session
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
from src.faturacao.schemas import (
    FaturaCreate,
    FaturaItemCreate,
    MetodoPagamento,
    ParcelaCreate,
)
from src.pacientes.models import Paciente, PlanoTratamento
from src.consultas.models import Consulta, ConsultaItem


def get_fatura(db: Session, fatura_id: int) -> Fatura:
    f = db.get(Fatura, fatura_id)
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
    # 1) validar paciente

    paciente = db.get(Paciente, payload.paciente_id)
    if not paciente:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Paciente não encontrado")

    # 2) validar campos por tipo e obter origem
    consulta = None
    plano = None
    if payload.tipo == FaturaTipo.consulta.value:
        # fatura de consulta: CONSULTA_ID obrigatório, PLANO_ID deve ser None
        if payload.consulta_id is None:
            raise HTTPException(400, "Deves enviar consulta_id para fatura de consulta")
        if payload.plano_id is not None:
            raise HTTPException(400, "Fatura de consulta não pode ter plano_id")
        consulta = db.get(Consulta, payload.consulta_id)
        if not consulta:
            raise HTTPException(404, "Consulta não encontrada")
    elif payload.tipo == FaturaTipo.plano.value:
        # fatura de plano: PLANO_ID obrigatório, CONSULTA_ID deve ser None
        if payload.plano_id is None:
            raise HTTPException(400, "Deves enviar plano_id para fatura de plano")
        if payload.consulta_id is not None:
            raise HTTPException(400, "Fatura de plano não pode ter consulta_id")
        plano = db.get(PlanoTratamento, payload.plano_id)
        if not plano:
            raise HTTPException(404, "Plano de tratamento não encontrado")
    

        # 2.1) evitar geração duplicada de fatura de plano
        existing = (
            db.query(Fatura)
              .filter(Fatura.plano_id == payload.plano_id)
              .filter(Fatura.estado.in_([FaturaEstado.pendente, FaturaEstado.parcial]))
              .first()
        )
        if existing:
            # Já existe fatura de plano em aberto, retorna esta
            return existing
    else:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, 
            f"Tipo de fatura inválido: {payload.tipo}"
        )
 
    # 3) criar fatura inicial
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

    # 4) gerar itens automaticamente
    total = 0

    if payload.tipo == FaturaTipo.consulta.value:
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
        # 1) buscamos o último orçamento aprovado deste paciente
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

        # 2) iteramos sobre os OrcamentoItem desse orçamento
        total = 0
        for pi in plano.itens:
            # obter preço e quantidade inicialmente aprovados
            oi = db.get(OrcamentoItem, pi.orcamento_item_id)
            if not oi:
                continue  # ignora itens sem orcamento associado
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

    else:
        # se alguém invocar com um tipo estranho…
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Tipo de fatura inválido: {payload.tipo}"
        )


    # 5) atualizar total da fatura
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
    observacoes: Optional[str] = None
) -> ParcelaPagamento:
    parc = db.get(ParcelaPagamento, parcela_id)
    if not parc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            f"Parcela com ID={parcela_id} não encontrada"
        )

    # 1) atualizar valor pago, método e data
    parc.valor_pago = valor_pago
    parc.data_pagamento = data_pagamento or datetime.utcnow()
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
    soma_pago = sum(p.valor_pago or 0 for p in fatura.parcelas)

    if soma_pago >= float(fatura.total):
        fatura.estado = FaturaEstado.paga
    elif soma_pago > 0:
        fatura.estado = FaturaEstado.parcial
    else:
        fatura.estado = FaturaEstado.pendente

    db.commit()
    db.refresh(parc)
    return parc


def pay_fatura_direto(
    db: Session,
    fatura_id: int,
    valor_pago: float,
    metodo_pagamento: MetodoPagamento,
    data_pagamento: Optional[datetime] = None,
    observacoes: Optional[str] = None
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
        metodo_pagamento=metodo_pagamento,
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
    
    db.commit()
    db.refresh(fatura)
    return fatura