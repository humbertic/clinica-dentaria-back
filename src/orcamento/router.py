# src/orcamento/router.py
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from src.database import SessionLocal
from typing import List, Optional
from datetime import date

from src.orcamento import service as svc
from src.orcamento.schemas import (
    OrcamentoCreate,
    OrcamentoRead,
    OrcamentoItemCreate,
    OrcamentoItemRead,
    OrcamentoUpdate,
    OrcamentoUpdateEstado,
    EstadoOrc
)

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ─────────────────────────────────────────────────────────────
#   Cabeçalho do orçamento
# ─────────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=OrcamentoRead,
    status_code=status.HTTP_201_CREATED,
)
def criar_orcamento(
    payload: OrcamentoCreate, db: Session = Depends(get_db)
):
    """
    Cria um orçamento em **rascunho** sem itens.
    """
    return svc.create_orcamento(db, payload)


@router.get("", response_model=List[OrcamentoRead])
def listar_orcamentos(
    paciente_id: Optional[int] = None,
    entidade_id: Optional[int] = None,
    estado: Optional[EstadoOrc] = None,
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    limit: Optional[int] = Query(None, gt=0, lt=100),
    db: Session = Depends(get_db),
):
    """
    Lista orçamentos com filtros opcionais.
    Se nenhum filtro for fornecido, retorna todos os orçamentos.
    """
    return svc.list_orcamentos(
        db, paciente_id, entidade_id, estado, 
        data_inicio, data_fim, limit
    )
    
    
@router.get("/paciente/{paciente_id}", response_model=List[OrcamentoRead])
def listar_orcamentos_por_paciente(
    paciente_id: int,
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    db: Session = Depends(get_db),
):
    """
    Lista orçamentos para um paciente específico.
    """
    return svc.get_orcamentos_by_paciente(db, paciente_id, data_inicio, data_fim)


@router.get("/estado/{estado}", response_model=List[OrcamentoRead])
def listar_orcamentos_por_estado(
    estado: EstadoOrc,
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    db: Session = Depends(get_db),
):
    """
    Lista orçamentos com um estado específico.
    """
    return svc.get_orcamentos_by_estado(db, estado, data_inicio, data_fim)


@router.get("/recentes", response_model=List[OrcamentoRead])
def listar_orcamentos_recentes(
    dias: int = Query(30, gt=0, lt=365),
    db: Session = Depends(get_db),
):
    """
    Lista orçamentos dos últimos X dias.
    """
    return svc.get_recent_orcamentos(db, dias)


@router.get("/{orc_id}", response_model=OrcamentoRead)
def obter_orcamento(
    orc_id: int, db: Session = Depends(get_db)
):
    """
    Devolve o orçamento completo, incluindo itens.
    """
    return svc.get_orcamento(db, orc_id)


@router.put("/{orc_id}/estado", response_model=OrcamentoRead)
def mudar_estado(
    orc_id: int,
    body: OrcamentoUpdateEstado,
    db: Session = Depends(get_db),
):
    """
    Muda o estado para **aprovado** ou **rejeitado**.
    Só permitido se regras de negócio forem cumpridas.
    """
    return svc.set_estado(db, orc_id, body.estado)

@router.put("/{orcamento_id}", response_model=OrcamentoRead)
def atualizar_orcamento_endpoint(
    orcamento_id: int, 
    dados: OrcamentoUpdate, 
    db: Session = Depends(get_db)
):
    """
    Atualiza um orçamento existente.
    
    Regras:
    - Entidade só pode ser alterada se não houver itens
    - Apenas orçamentos em estado 'rascunho' podem ser alterados
    """
    return svc.atualizar_orcamento(db, orcamento_id, dados)

# ─────────────────────────────────────────────────────────────
#   Itens do orçamento
# ─────────────────────────────────────────────────────────────

@router.post(
    "/{orc_id}/itens",
    response_model=OrcamentoItemRead,
    status_code=status.HTTP_201_CREATED,
)
def adicionar_item(
    orc_id: int,
    item: OrcamentoItemCreate,
    db: Session = Depends(get_db),
):
    """
    Adiciona linha ao orçamento (só se estiver em rascunho).
    Calcula subtotais e actualiza totais do cabeçalho.
    """
    return svc.add_item(db, orc_id, item)


@router.delete(
    "/{orc_id}/itens/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remover_item(
    orc_id: int,
    item_id: int,
    db: Session = Depends(get_db),
):
    """
    Remove linha do orçamento e recalcula totais.
    """
    svc.delete_item(db, orc_id, item_id)
