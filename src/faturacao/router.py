from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.params import Query
from sqlalchemy.orm import Session
from typing import List, Optional

from src.database import SessionLocal
from src.utilizadores.dependencies import get_current_user
from src.utilizadores.models import Utilizador

from src.faturacao import service, schemas
from src.faturacao.models import FaturaTipo, FaturaEstado

router = APIRouter(
    prefix="/faturas",
    tags=["Faturação"],
    responses={404: {"description": "Não encontrado"}},
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=List[schemas.FaturaRead], summary="Listar faturas")
def listar_faturas(
    paciente_id: int = None,
    tipo: FaturaTipo = None,
    estado: FaturaEstado = None,
    db: Session = Depends(get_db),
    utilizador: Utilizador = Depends(get_current_user),
):
    return service.list_faturas(db, paciente_id, tipo, estado)


@router.get("/{fatura_id}", response_model=schemas.FaturaRead, summary="Obter fatura por ID")
def obter_fatura(
    fatura_id: int,
    db: Session = Depends(get_db),
    utilizador: Utilizador = Depends(get_current_user),
):
    return service.get_fatura(db, fatura_id)


@router.post("", response_model=schemas.FaturaRead, status_code=status.HTTP_201_CREATED, summary="Criar nova fatura")
def criar_fatura(
    payload: schemas.FaturaCreate,
    db: Session = Depends(get_db),
    utilizador: Utilizador = Depends(get_current_user),
):
    return service.create_fatura(db, payload)


@router.post("/{fatura_id}/itens", response_model=schemas.FaturaItemRead, status_code=status.HTTP_201_CREATED, summary="Adicionar item à fatura")
def adicionar_item(
    fatura_id: int,
    payload: schemas.FaturaItemCreate,
    db: Session = Depends(get_db),
    utilizador: Utilizador = Depends(get_current_user),
):
    return service.add_item(db, fatura_id, payload)


@router.post("/{fatura_id}/parcelas", response_model=List[schemas.ParcelaRead], status_code=status.HTTP_201_CREATED, summary="Definir parcelas para fatura de plano")
def definir_parcelas(
    fatura_id: int,
    payload: List[schemas.ParcelaCreate],
    db: Session = Depends(get_db),
    utilizador: Utilizador = Depends(get_current_user),
):
    return service.generate_parcelas(db, fatura_id, payload)


@router.post("/parcelas/{parcela_id}/pagamento", response_model=schemas.ParcelaRead, summary="Registar pagamento de parcela")
def pagar_parcela(
    parcela_id: int,
    pagamento: schemas.ParcelaPagamentoRequest,
    session_id: Optional[int] = Query(None, description="ID da sessão de pagamento"),
    db: Session = Depends(get_db),
    utilizador: Utilizador = Depends(get_current_user),
):
    return service.pay_parcela(
        db=db,
        parcela_id=parcela_id,
        valor_pago=pagamento.valor_pago,
        metodo_pagamento=pagamento.metodo_pagamento,
        data_pagamento=pagamento.data_pagamento,
        observacoes=pagamento.observacoes if hasattr(pagamento, 'observacoes') else None,
        session_id=session_id,
        operador_id= utilizador.id if session_id else None
    )


@router.post("/{fatura_id}/pagamento-direto", response_model=schemas.FaturaRead)
def pagar_fatura_direto(
    fatura_id: int,
    pagamento: schemas.ParcelaPagamentoRequest,
    session_id: Optional[int] = Query(None, description="ID da sessão de pagamento"),
    db: Session = Depends(get_db),
    utilizador: Utilizador = Depends(get_current_user),
):
    """
    Process a direct payment to an invoice without parcelas
    """
    return service.pay_fatura_direto(
        db=db,
        fatura_id=fatura_id,
        valor_pago=pagamento.valor_pago,
        metodo_pagamento=pagamento.metodo_pagamento,
        data_pagamento=pagamento.data_pagamento,
        observacoes=pagamento.observacoes if hasattr(pagamento, 'observacoes') else None,
        session_id=session_id,
        operador_id= utilizador.id if session_id else None
    )