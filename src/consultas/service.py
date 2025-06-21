from sqlalchemy.orm import Session,joinedload
from sqlalchemy import func
from fastapi import HTTPException, status
from typing import Optional, List
from datetime import date, datetime
from src.marcacoes.models import Marcacao
from src.orcamento.models import Orcamento, OrcamentoItem
from src.consultas.models import Consulta, ConsultaItem
from src.auditoria.utils import registrar_auditoria

from src.consultas.schemas import (
    ConsultaCreate,
    ConsultaUpdate,
    ConsultaItemCreate,
    ConsultaItemUpdate,
)
from src.pacientes.models import Paciente, PlanoItem, PlanoTratamento
from src.clinica.models import Clinica
from src.utilizadores.models import Utilizador
from src.entidades.models import Entidade
from src.artigos.models import ArtigoMedico
from src.precos.models import Preco


def get_consulta(db: Session, consulta_id: int) -> Consulta:
    consulta = db.get(Consulta, consulta_id)
    if not consulta:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            f"Consulta com ID={consulta_id} não encontrada"
        )
    return consulta


def get_item(db: Session, item_id: int) -> ConsultaItem:
    item = db.get(ConsultaItem, item_id)
    if not item:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            f"Item de consulta com ID={item_id} não encontrado"
        )
    return item


def create_consulta(
    db: Session,
    payload: ConsultaCreate
) -> Consulta:
    # 1) Validar existência das FKs
    if not db.get(Paciente, payload.paciente_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Paciente não encontrado")
    if not db.get(Clinica, payload.clinica_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Clínica não encontrada")
    if not db.get(Entidade, payload.entidade_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Entidade não encontrada")
    if payload.medico_id and not db.get(Utilizador, payload.medico_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Médico não encontrado")

    # 2) Criar a consulta
    consulta = Consulta(**payload.dict())
    db.add(consulta)
    db.commit()
    db.refresh(consulta)
    
    # 3) Verificar se existe um plano de tratamento ATIVO para o paciente
    plano_ativo = (
        db.query(PlanoTratamento)
        .filter(
            PlanoTratamento.paciente_id == payload.paciente_id,
            PlanoTratamento.estado == "em_curso"  # Apenas planos ativos
        )
        .first()
    )
    
    # 4) Se não existir plano ativo, verificar se há orçamentos aprovados
    if not plano_ativo:
        create_treatment_plan_from_orcamentos(db, payload.paciente_id)
    
    return consulta

def create_treatment_plan_from_orcamentos(
    db: Session, 
    paciente_id: int
) -> Optional[int]:
    """
    Creates a treatment plan for a patient based on approved orcamentos that don't have a plan yet.
    
    Args:
        db: Database session
        paciente_id: Patient ID
        
    Returns:
        The ID of the created plan, or None if no plan was created
    """
    # Find approved orcamentos for this patient that aren't already in a plan
    orcamentos_aprovados = (
        db.query(Orcamento)
        .filter(
            Orcamento.paciente_id == paciente_id,
            Orcamento.estado == "aprovado",
        )
        .all()
    )
    
    # Filter out orcamentos that already have items in a plan
    filtered_orcamentos = []
    for orcamento in orcamentos_aprovados:
        # Check if any items from this orcamento are already in a plan
        items_in_plan = (
            db.query(OrcamentoItem)
            .join(
                PlanoItem, 
                PlanoItem.orcamento_item_id == OrcamentoItem.id
            )
            .filter(
                OrcamentoItem.orcamento_id == orcamento.id
            )
            .count()
        )
        
        # If no items are in a plan, include this orcamento
        if items_in_plan == 0:
            filtered_orcamentos.append(orcamento)
    
    if not filtered_orcamentos:
        return None
    
    # Create a new treatment plan
    novo_plano = PlanoTratamento(
        paciente_id=paciente_id,
        estado="em_curso",
        data_criacao=datetime.now()
    )
    db.add(novo_plano)
    db.flush()
    
    # Create plan items from all approved orcamentos
    for orcamento in filtered_orcamentos:
        itens_orcamento = (
            db.query(OrcamentoItem)
            .filter(OrcamentoItem.orcamento_id == orcamento.id)
            .all()
        )
        
        for item_orcamento in itens_orcamento:
            item_plano = PlanoItem(
                plano_id=novo_plano.id,
                orcamento_item_id=item_orcamento.id,
                artigo_id=item_orcamento.artigo_id,
                quantidade_prevista=item_orcamento.quantidade,
                numero_dente=item_orcamento.numero_dente,
                face=item_orcamento.face,
                quantidade_executada=0,
                estado="pendente"
            )
            db.add(item_plano)
    
    db.commit()
    return novo_plano.id

def close_associated_marcacao(db: Session, consulta_id: int, paciente_id: int) -> Optional[Marcacao]:
    """
    Find and close the active appointment (marcacao) for a patient when completing a consultation.
    
    Args:
        db: Database session
        consulta_id: ID of the consultation being completed
        paciente_id: ID of the patient
        
    Returns:
        The updated Marcacao object or None if no matching appointment was found
    """
    marcacao = (
        db.query(Marcacao)
          .filter(
              Marcacao.paciente_id == paciente_id,
              Marcacao.estado == "iniciada"
          )
          .first()
    )
    
    if marcacao:
        marcacao.estado = "concluida"
        db.commit()
        db.refresh(marcacao)
        
        registrar_auditoria(
            db,
            utilizador_id=marcacao.medico_id,  
            acao="Atualização",
            objeto="Marcacao",
            objeto_id=marcacao.id,
            detalhes=f"Marcação #{marcacao.id} concluída ao finalizar consulta #{consulta_id}"
        )
        
    return marcacao


def update_consulta(db: Session, consulta_id: int, data: ConsultaUpdate, utilizador_id: int) -> Consulta:
    consulta = get_consulta(db, consulta_id)
    
    for field, value in data.dict(exclude_unset=True).items():
        setattr(consulta, field, value)
    
    if data.estado == "concluida":
        close_associated_marcacao(db, consulta_id, consulta.paciente_id)
    
    db.commit()
    db.refresh(consulta)
    
    registrar_auditoria(
        db,
        utilizador_id,
        "Atualização",
        "Consulta",
        consulta_id,
        f"Consulta #{consulta_id} atualizada. Novo estado: {consulta.estado}"
    )
    
    return consulta


def add_item(
    db: Session,
    consulta_id: int,
    payload: ConsultaItemCreate
) -> ConsultaItem:
    # 1) Verificar existência da consulta
    consulta = get_consulta(db, consulta_id)

    # 2) Verificar existência do artigo
    artigo = db.get(ArtigoMedico, payload.artigo_id)
    if not artigo:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            f"Artigo com ID={payload.artigo_id} não encontrado"
        )

    # 3) Validar requisitos de dente/face
    if artigo.requer_dente and payload.numero_dente is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Este artigo requer número de dente"
        )
    if artigo.requer_face and not payload.face:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Este artigo requer indicação de face(s) do dente"
        )

    # 4) Obter o preço conforme a entidade da consulta
    preco = (
        db.query(Preco)
          .filter_by(artigo_id=artigo.id, entidade_id=consulta.entidade_id)
          .first()
    )
    if not preco:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Preço para este artigo e entidade não encontrado"
        )

    valor_unit = float(preco.valor_paciente)
    total = payload.quantidade * valor_unit

    # 5) Criar o item
    item = ConsultaItem(
        consulta_id     = consulta.id,
        artigo_id        = artigo.id,
        quantidade       = payload.quantidade,
        preco_unitario   = valor_unit,
        total            = total,
        numero_dente     = payload.numero_dente,
        face             = payload.face,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_item(
    db: Session,
    item_id: int,
    changes: ConsultaItemUpdate
) -> ConsultaItem:
    item = get_item(db, item_id)
    consulta = item.consulta  # já carregado pelo relationship

    data = changes.dict(exclude_unset=True)

    # 1) Se trocar artigo, valida novo artigo
    if "artigo_id" in data:
        artigo = db.get(ArtigoMedico, data["artigo_id"])
        if not artigo:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                f"Artigo com ID={data['artigo_id']} não encontrado"
            )
        item.artigo_id = data.pop("artigo_id")

    # 2) Atualizar atributos livres
    if "quantidade" in data:
        item.quantidade = data["quantidade"]
    if "numero_dente" in data:
        item.numero_dente = data["numero_dente"]
    if "face" in data:
        item.face = data["face"]

    # 3) Atualizar preço unitário
    if "preco_unitario" in data:
        item.preco_unitario = data["preco_unitario"]
    else:
        # recalcula de acordo com Preco
        preco = (
            db.query(Preco)
              .filter_by(
                  artigo_id=item.artigo_id,
                  entidade_id=consulta.entidade_id
              ).first()
        )
        if not preco:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "Preço não encontrado para artigo/entidade"
            )
        item.preco_unitario = float(preco.valor_paciente)

    # 4) Recalcular total
    item.total = item.quantidade * float(item.preco_unitario)

    db.commit()
    db.refresh(item)
    return item





def list_consultas(
    db: Session,
    clinica_id: int,
    medico_id: Optional[int] = None,
    paciente_id: Optional[int] = None,
    entidade_id: Optional[int] = None,
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    estado: Optional[str] = None,
) -> List[Consulta]:
    # Usando joinedload para carregar os itens relacionados
    q = db.query(Consulta).options(
        joinedload(Consulta.itens).joinedload(ConsultaItem.artigo)
    ).filter(Consulta.clinica_id == clinica_id)
    
    # Resto do código permanece igual
    if medico_id:
        q = q.filter(Consulta.medico_id == medico_id)
    if paciente_id:
        q = q.filter(Consulta.paciente_id == paciente_id)
    if entidade_id:
        q = q.filter(Consulta.entidade_id == entidade_id)
    if data_inicio:
        q = q.filter(func.date(Consulta.data_inicio) >= data_inicio)
    if data_fim:
        q = q.filter(func.date(Consulta.data_inicio) <= data_fim)
    if estado:
        q = q.filter(Consulta.estado == estado)
    
    return q.order_by(Consulta.data_inicio.desc()).all()


def delete_item(db: Session, item_id: int) -> bool:
    """
    Remove um item de consulta
    
    Args:
        db: Sessão do banco de dados
        item_id: ID do item a ser removido
        
    Returns:
        True se o item foi removido com sucesso
        
    Raises:
        HTTPException: Se o item não for encontrado
    """
    item = get_item(db, item_id)
    
    # Verificar se a consulta está em um estado que permite edição
    if item.consulta.estado == "concluida":
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Não é possível remover itens de uma consulta concluída"
        )
    
    db.delete(item)
    db.commit()
    return True