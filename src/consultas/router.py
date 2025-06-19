from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from src.database import SessionLocal
from src.utilizadores.dependencies import get_current_user
from src.utilizadores.models import Utilizador

from src.consultas import service, schemas

router = APIRouter(
    prefix="/consultas",
    tags=["Consultas"],
    responses={404: {"description": "Não encontrado"}},
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post(
    "",
    response_model=schemas.ConsultaFull,
    status_code=status.HTTP_201_CREATED,
    summary="Iniciar nova consulta",
)
def criar_consulta(
    payload: schemas.ConsultaCreate,
    db: Session = Depends(get_db),
    utilizador_atual: Utilizador = Depends(get_current_user),
):
    """
    Cria uma nova consulta. 
    Campos obrigatórios: paciente_id, clinica_id, entidade_id; medico_id é opcional.
    """
    return service.create_consulta(db, payload)


@router.get(
    "",
    response_model=List[schemas.ConsultaFull],
    summary="Listar consultas",
)
def listar_consultas(
    clinica_id: int = Query(..., description="ID da clínica (obrigatório)"),
    medico_id: Optional[int] = Query(None, description="ID do médico"),
    paciente_id: Optional[int] = Query(None, description="ID do paciente"),
    entidade_id: Optional[int] = Query(None, description="ID da entidade"),
    data_inicio: Optional[date] = Query(None, description="Data mínima"),
    data_fim: Optional[date] = Query(None, description="Data máxima"),
    estado: Optional[str] = Query(None, description="Estado da consulta"),
    
    db: Session = Depends(get_db),
    utilizador_atual: Utilizador = Depends(get_current_user),
):
    """
    Lista todas as consultas filtrando por clínica (obrigatório) e demais filtros opcionais.
    """
    return service.list_consultas(
        db,
        clinica_id=clinica_id,
        medico_id=medico_id,
        paciente_id=paciente_id,
        entidade_id=entidade_id,
        data_inicio=data_inicio,
        data_fim=data_fim,
        estado=estado,
    )
    
    
@router.get(
    "/{consulta_id}",
    response_model=schemas.ConsultaFull,
    summary="Obter consulta por ID",
)
def obter_consulta(
    consulta_id: int,
    db: Session = Depends(get_db),
    utilizador_atual: Utilizador = Depends(get_current_user),
):
    """
    Retorna os detalhes de uma consulta específica, incluindo todos os seus itens.
    """
    return service.get_consulta(db, consulta_id)


@router.put(
    "/{consulta_id}",
    response_model=schemas.ConsultaFull,
    summary="Atualizar dados da consulta",
)
def atualizar_consulta(
    consulta_id: int,
    changes: schemas.ConsultaUpdate,
    db: Session = Depends(get_db),
    utilizador_atual: Utilizador = Depends(get_current_user),
):
    """
    Atualiza apenas os campos fornecidos na consulta.
    """
    return service.update_consulta(db, consulta_id, changes, utilizador_atual.id)


@router.post(
    "/{consulta_id}/itens",
    response_model=schemas.ConsultaItemRead,
    status_code=status.HTTP_201_CREATED,
    summary="Adicionar item à consulta",
)
def adicionar_item(
    consulta_id: int,
    payload: schemas.ConsultaItemCreate,
    db: Session = Depends(get_db),
    utilizador_atual: Utilizador = Depends(get_current_user),
):
    """
    Adiciona um artigo/procedimento à consulta.
    Valida requisitos de dente/face e aplica o preço correto.
    """
    return service.add_item(db, consulta_id, payload)


@router.get(
    "/itens/{item_id}",
    response_model=schemas.ConsultaItemRead,
    summary="Obter item de consulta por ID",
)
def obter_item(
    item_id: int,
    db: Session = Depends(get_db),
    utilizador_atual: Utilizador = Depends(get_current_user),
):
    """
    Retorna os detalhes de um item de consulta específico.
    """
    return service.get_item(db, item_id)


@router.put(
    "/itens/{item_id}",
    response_model=schemas.ConsultaItemRead,
    summary="Atualizar item de consulta",
)
def atualizar_item(
    item_id: int,
    changes: schemas.ConsultaItemUpdate,
    db: Session = Depends(get_db),
    utilizador_atual: Utilizador = Depends(get_current_user),
):
    """
    Atualiza apenas os campos fornecidos de um item de consulta.
    """
    return service.update_item(db, item_id, changes)


@router.delete("/itens/{item_id}", response_model=bool)
async def delete_consulta_item(
    item_id: int,
    db: Session = Depends(get_db),
    utilizador_atual: Utilizador = Depends(get_current_user),
):
    """
    Remove um item de consulta
    """
    return service.delete_item(db, item_id)
