from fastapi import APIRouter, Depends, HTTPException, Response, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from src.database import SessionLocal
from src.utilizadores.dependencies import get_current_user
from src.utilizadores.models import Utilizador

from . import service, schemas

router = APIRouter(
    prefix="/marcacoes",
    tags=["Marcações"],
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
    response_model=schemas.MarcacaoRead,
    status_code=status.HTTP_201_CREATED,
    summary="Agendar nova consulta",
)
def criar_marcacao(
    payload: schemas.MarcacaoCreate,
    db: Session = Depends(get_db),
    utilizador_atual: Utilizador = Depends(get_current_user),
):
    """
    Cria uma nova marcação com estado 'agendada'.
    Valida Paciente, Médico, Clínica, Entidade e utilizador que agendou.
    """
    return service.create_marcacao(db, payload, utilizador_atual.id)


@router.get(
    "",
    response_model=List[schemas.MarcacaoRead],
    summary="Listar marcações",
)
def listar_marcacoes_endpoint(
    clinica_id: int               = Query(..., description="ID da clínica (obrigatório)"),
    medico_id: Optional[int]      = Query(None, description="ID do médico"),
    paciente_id: Optional[int]    = Query(None, description="ID do paciente"),
    entidade_id: Optional[int]    = Query(None, description="ID da entidade"),
    data_inicio: Optional[date]   = Query(None, description="Data mínima"),
    data_fim: Optional[date]      = Query(None, description="Data máxima"),
    estado: Optional[str]         = Query(None, description="Estado da marcação"),
    db: Session                   = Depends(get_db),
):
    """
    Lista todas as marcações filtrando por clínica (obrigatório) e demais filtros opcionais.
    """
    return service.list_marcacoes(
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
    "/{marc_id}",
    response_model=schemas.MarcacaoRead,
    summary="Obter marcação por ID",
)
def obter_marcacao(
    marc_id: int,
    db: Session                   = Depends(get_db),
    utilizador_atual: Utilizador  = Depends(get_current_user),
):
    """
    Retorna detalhes de uma marcação específica.
    """
    return service.get_marcacao(db, marc_id)


@router.put(
    "/{marc_id}",
    response_model=schemas.MarcacaoRead,
    summary="Atualizar marcação",
)
def atualizar_marcacao(
    marc_id: int,
    payload: schemas.MarcacaoUpdate,
    db: Session                   = Depends(get_db),
    utilizador_atual: Utilizador  = Depends(get_current_user),
):
    """
    Atualiza campos de uma marcação (paciente, médico, clínica, entidade,
    data_hora, observações e/ou estado).
    """
    return service.update_marcacao(db, marc_id, payload)


@router.put(
    "/{marc_id}/estado",
    response_model=schemas.MarcacaoRead,
    summary="Alterar estado da marcação",
)
def mudar_estado(
    marc_id: int,
    payload: schemas.MarcacaoUpdate,  # neste caso usamos apenas o campo `estado`
    db: Session                   = Depends(get_db),
    utilizador_atual: Utilizador  = Depends(get_current_user),
):
    """
    Atualiza apenas o estado da marcação para um dos valores:
    'rascunho', 'agendada', 'checada', 'concluída', 'cancelada'.
    """
    if not payload.estado:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Deve especificar um novo estado."
        )
    return service.set_estado(db, marc_id, payload.estado)



@router.delete(
    "/{marc_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover marcação",
)
def remover_marcacao(
    marc_id: int,
    db: Session                    = Depends(get_db),
    utilizador_atual: Utilizador   = Depends(get_current_user),
):
    """
    Exclui permanentemente a marcação especificada.
    """
    service.delete_marcacao(db, marc_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)