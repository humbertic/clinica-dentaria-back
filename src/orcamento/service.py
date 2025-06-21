from decimal import Decimal
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from datetime import date, timedelta

from src.database import SessionLocal
from src.orcamento.schemas import (
    OrcamentoCreate,
    OrcamentoRead,
    OrcamentoItemCreate,
    OrcamentoItemRead,
    EstadoOrc,
    OrcamentoUpdate,
)
from src.orcamento.models import Orcamento, OrcamentoItem
from src.pacientes.models import Paciente
from src.entidades.models import Entidade
from src.artigos.models import ArtigoMedico
from src.precos.models import Preco
from sqlalchemy.orm import joinedload


# ───────────────────────────────────────────────────────────────
#    Helpers internos
# ───────────────────────────────────────────────────────────────

def _get_preco(db: Session, artigo_id: int, entidade_id: int) -> Preco:
    preco = (
        db.query(Preco)
        .filter_by(artigo_id=artigo_id, entidade_id=entidade_id)
        .one_or_none()
    )
    if not preco:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Preço não definido para o artigo e entidade seleccionados.",
        )
    return preco


def _recalc_totais(orc: Orcamento) -> None:
    """Actualiza os totais do cabeçalho com base nos itens."""
    orc.total_entidade = sum(i.subtotal_entidade for i in orc.itens) or Decimal("0")
    orc.total_paciente = sum(i.subtotal_paciente for i in orc.itens) or Decimal("0")


# ───────────────────────────────────────────────────────────────
#    Funções públicas
# ───────────────────────────────────────────────────────────────

def create_orcamento(db: Session, data: OrcamentoCreate) -> Orcamento:
    # confirma FK
    if not db.get(Paciente, data.paciente_id):
        raise HTTPException(404, "Paciente não encontrado")
    if not db.get(Entidade, data.entidade_id):
        raise HTTPException(404, "Entidade não encontrada")

    orc = Orcamento(
        paciente_id=data.paciente_id,
        entidade_id=data.entidade_id,
        data=data.data,
        observacoes=data.observacoes,
    )
    db.add(orc)
    db.commit()
    db.refresh(orc)
    return orc


def get_orcamento(db: Session, orc_id: int) -> Orcamento:
    orc = db.query(Orcamento).options(
        joinedload(Orcamento.paciente),
        joinedload(Orcamento.entidade),
        joinedload(Orcamento.itens).joinedload(OrcamentoItem.artigo),
    ).filter(Orcamento.id == orc_id).first()
    if not orc:
        raise HTTPException(404, "Orçamento não encontrado")
    return orc


def list_orcamentos(
    db: Session,
    paciente_id: Optional[int] = None,
    entidade_id: Optional[int] = None,
    estado: Optional[EstadoOrc] = None,
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    limit: Optional[int] = None,
) -> List[Orcamento]:
    """Lista orçamentos com filtros opcionais."""
    q = db.query(Orcamento).options(
        joinedload(Orcamento.paciente),
        joinedload(Orcamento.entidade),
        joinedload(Orcamento.itens).joinedload(OrcamentoItem.artigo),
    )
    # Aplicar os filtros
    if paciente_id:
        q = q.filter_by(paciente_id=paciente_id)
    if entidade_id:
        q = q.filter_by(entidade_id=entidade_id)
    if estado:
        q = q.filter_by(estado=estado)
    if data_inicio:
        q = q.filter(Orcamento.data >= data_inicio)
    if data_fim:
        q = q.filter(Orcamento.data <= data_fim)
    
    # Ordenar por data mais recente
    q = q.order_by(Orcamento.data.desc())
    
    # Limitar resultados se especificado
    if limit:
        q = q.limit(limit)
        
    return q.all()


def get_orcamentos_by_paciente(
    db: Session, 
    paciente_id: int, 
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None
) -> List[Orcamento]:
    """Retorna orçamentos de um paciente específico, com período opcional."""
    return list_orcamentos(
        db, 
        paciente_id=paciente_id, 
        data_inicio=data_inicio, 
        data_fim=data_fim
    )

def get_orcamentos_by_estado(
    db: Session, 
    estado: EstadoOrc, 
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None
) -> List[Orcamento]:
    """Retorna orçamentos com um estado específico, com período opcional."""
    return list_orcamentos(
        db, 
        estado=estado, 
        data_inicio=data_inicio, 
        data_fim=data_fim
    )
    
def get_recent_orcamentos(db: Session, dias: int = 30) -> List[Orcamento]:
    """Retorna orçamentos dos últimos X dias."""
    data_inicio = date.today() - timedelta(days=dias)
    return list_orcamentos(db, data_inicio=data_inicio)

def add_item(db: Session, orc_id: int, item_in: OrcamentoItemCreate) -> OrcamentoItem:
    orc = get_orcamento(db, orc_id)
    if orc.estado != EstadoOrc.rascunho:
        raise HTTPException(400, "Só pode editar rascunho")

    artigo = db.get(ArtigoMedico, item_in.artigo_id)
    if not artigo:
        raise HTTPException(404, "Artigo não encontrado")

    # 1. Validação dente
    if artigo.requer_dente and not item_in.numero_dente:
        raise HTTPException(400, "Número de dente é obrigatório")

    # 2. Validação faces (lista)
    if artigo.requer_face:
        if not item_in.face or len(item_in.face) == 0:
            raise HTTPException(400, "Deve indicar pelo menos uma face")
        invalid = [f for f in item_in.face if f not in {"M","D","V","L","O","I"}]
        if invalid:
            raise HTTPException(400, f"Faces inválidas: {', '.join(invalid)}")
    else:
        item_in.face = None     # limpa se não precisa

    # 3. Quantidade fixada a 1
    quantidade = 1

    # 4. Verifica preço (artigo + entidade)
    preco = _get_preco(db, artigo.id, orc.entidade_id)

    item = OrcamentoItem(
        orcamento_id       = orc.id,
        artigo_id          = artigo.id,
        quantidade         = quantidade,
        preco_entidade     = preco.valor_entidade,
        preco_paciente     = preco.valor_paciente,
        subtotal_entidade  = preco.valor_entidade,
        subtotal_paciente  = preco.valor_paciente,
        numero_dente       = item_in.numero_dente,
        face              = item_in.face,      # array gravado
    )
    db.add(item)
    db.flush()
    db.refresh(orc)
    _recalc_totais(orc)
    db.commit()
    db.refresh(item)
    return item



def delete_item(db: Session, orc_id: int, item_id: int) -> None:
    orc = get_orcamento(db, orc_id)
    if orc.estado != EstadoOrc.rascunho:
        raise HTTPException(400, "Orçamento não está em rascunho")

    item = db.get(OrcamentoItem, item_id)
    if not item or item.orcamento_id != orc_id:
        raise HTTPException(404, "Item não encontrado")

    db.delete(item)
    db.flush()
    db.refresh(orc)
    _recalc_totais(orc)
    db.commit()


def set_estado(db: Session, orc_id: int, novo_estado: EstadoOrc) -> Orcamento:
    orc = get_orcamento(db, orc_id)

    if novo_estado == EstadoOrc.aprovado and not orc.itens:
        raise HTTPException(400, "Não é possível aprovar orçamento sem itens")

    orc.estado = novo_estado
    db.commit()
    db.refresh(orc)
    return orc


def atualizar_orcamento(db: Session, orc_id: int, dados: OrcamentoUpdate) -> Orcamento:
    """Atualiza dados de um orçamento. Regras especiais aplicadas para cada campo."""
    orc = get_orcamento(db, orc_id)
    
    # Verifica estado - só pode editar rascunhos
    if orc.estado != EstadoOrc.rascunho:
        raise HTTPException(400, "Só é possível editar orçamentos em rascunho")
    
    # Validação para alteração de entidade
    if dados.entidade_id is not None and dados.entidade_id != orc.entidade_id:
        # Verifica se tem itens
        if orc.itens:
            raise HTTPException(
                status_code=400,
                detail="Não é possível alterar a entidade de um orçamento que já possui itens"
            )
        
        # Verifica se a entidade existe
        if not db.get(Entidade, dados.entidade_id):
            raise HTTPException(404, "Entidade não encontrada")
            
        orc.entidade_id = dados.entidade_id
    
    # Campos que podem ser atualizados sempre
    if dados.data is not None:
        orc.data = dados.data
    
    if dados.observacoes is not None:
        orc.observacoes = dados.observacoes
    
    db.commit()
    db.refresh(orc)
    return orc

def get_orcamento_details(db: Session, orcamento_id: int):
    """
    Get detailed orçamento information including all relationships.
    """
    
    orcamento = (
        db.query(Orcamento)
        .options(
            joinedload(Orcamento.paciente),
            joinedload(Orcamento.entidade),
            joinedload(Orcamento.itens).joinedload(OrcamentoItem.artigo)
        )
        .filter(Orcamento.id == orcamento_id)
        .first()
    )
    
    return orcamento