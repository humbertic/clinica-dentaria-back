from typing import Optional, List
from datetime import date
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from src.marcacoes.models import Marcacao
from src.marcacoes.schemas import (
    MarcacaoCreate,
    MarcacaoRead,
    MarcacaoUpdate,
)
from src.pacientes.models import Paciente
from src.utilizadores.models import Utilizador
from src.clinica.models import Clinica
from src.entidades.models import Entidade


def _get_fk_or_404(db: Session, model, id: int, name: str):
    obj = db.get(model, id)
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"{name} não encontrado")
    return obj


def create_marcacao(
    db: Session,
    data: MarcacaoCreate,
    agendador_id: int                  
) -> Marcacao:
    # valida FKs
    _get_fk_or_404(db, Paciente,  data.paciente_id,  "Paciente")
    _get_fk_or_404(db, Clinica,    data.clinic_id,    "Clínica")
    _get_fk_or_404(db, Utilizador, agendador_id,      "Utilizador (agendador)")
    _get_fk_or_404(db, Entidade,   data.entidade_id,  "Entidade")

    # checa perfil de médico
    utilizador = _get_fk_or_404(db, Utilizador, data.medico_id, "Médico")
    is_doctor = any(
        uc.perfil.perfil.lower() == "doctor"
        for uc in utilizador.perfis
        if uc.perfil is not None
    )
    if not is_doctor:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "O utilizador selecionado não tem perfil de médico."
        )

    # cria marcacao (estado e timestamps geridos pelo model)
    payload = data.dict(exclude={"estado", "agendada_por"})
    m = Marcacao(**payload, agendada_por=agendador_id)
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


def get_marcacao(db: Session, marc_id: int) -> Marcacao:
    m = db.get(Marcacao, marc_id)
    if not m:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Marcação não encontrada")
    return m


def list_marcacoes(
    db: Session,
    clinica_id: int,
    medico_id: Optional[int] = None,
    paciente_id: Optional[int] = None,
    entidade_id: Optional[int] = None,
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    estado: Optional[str] = None,
) -> List[Marcacao]:
    q = db.query(Marcacao).filter(Marcacao.clinic_id == clinica_id)
    if medico_id:
        q = q.filter(Marcacao.medico_id == medico_id)
    if paciente_id:
        q = q.filter(Marcacao.paciente_id == paciente_id)
    if entidade_id:
        q = q.filter(Marcacao.entidade_id == entidade_id)
    if data_inicio:
        q = q.filter(func.date(Marcacao.data_hora_inicio) >= data_inicio)
    if data_fim:
        q = q.filter(func.date(Marcacao.data_hora_inicio) <= data_fim)
    if estado:
        q = q.filter(Marcacao.estado == estado)
    return q.order_by(Marcacao.data_hora_inicio).all()


def update_marcacao(
    db: Session,
    marc_id: int,
    changes: MarcacaoUpdate
) -> Marcacao:
    m = get_marcacao(db, marc_id)

    # atualiza apenas campos fornecidos
    updates = changes.dict(exclude_unset=True)
    for field, val in updates.items():
        setattr(m, field, val)

    db.commit()
    db.refresh(m)
    return m


def set_estado(
    db: Session,
    marc_id: int,
    novo_estado: str
) -> Marcacao:
    m = get_marcacao(db, marc_id)
    m.estado = novo_estado
    db.commit()
    db.refresh(m)
    return m




def delete_marcacao(
    db: Session,
    marc_id: int
) -> None:
    """
    Remove a marcação com o ID especificado, apenas se estiver no estado 'agendada'.
    """
    m = get_marcacao(db, marc_id)
    if m.estado.lower() != "agendada":
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Só marcações com estado 'agendada' podem ser eliminadas."
        )
    db.delete(m)
    db.commit()

