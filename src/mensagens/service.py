# src/mensagens/service.py
from datetime import datetime
from typing import Optional
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload
from src.mensagens import models, schemas
from src.utilizadores.models import Utilizador, UtilizadorClinica


# ---------- helpers -------------------------------------------------
def _ordenar(a: int, b: int) -> tuple[int, int]:
    return (a, b) if a < b else (b, a)


def _get_or_create_thread(
    db: Session,
    user_a: int,
    user_b: int,
    clinica_id: int
) -> models.Thread:
    a, b = _ordenar(user_a, user_b)
    thread = (
        db.query(models.Thread)
          .filter_by(
              clinica_id=clinica_id,
              participante_a_id=a,
              participante_b_id=b
          )
          .first()
    )
    if thread:
        return thread

    thread = models.Thread(
        clinica_id=clinica_id,
        participante_a_id=a,
        participante_b_id=b
    )
    db.add(thread)
    db.commit()
    db.refresh(thread)
    return thread


# ---------- operações públicas -------------------------------------
def criar_mensagem(
    db: Session,
    remetente: Utilizador,
    dados: schemas.MessageCreate
) -> models.Mensagem:
    # Check if thread already exists
    if dados.thread_id:
        thread = db.query(models.Thread).get(dados.thread_id)
        if not thread:
            raise ValueError("Thread inexistente.")
            
        # For DMs, check if user is a participant
        if thread.tipo == "dm" and remetente.id not in (
            thread.participante_a_id, thread.participante_b_id
        ):
            raise PermissionError("Utilizador não pertence à thread.")
            
        # For any thread, check if user belongs to the clinic
        if thread.clinica_id != dados.clinica_id:
            raise PermissionError("Thread pertence a outra clínica.")
            
        # For clinic threads, verify user belongs to the clinic
        if thread.tipo in ["clinic", "group"]:
            is_member = db.query(UtilizadorClinica).filter_by(
                utilizador_id=remetente.id,
                clinica_id=dados.clinica_id
            ).first() is not None
            
            if not is_member:
                raise PermissionError("Utilizador não pertence a esta clínica.")
    else:
        # Create a new thread based on the type
        if dados.tipo_thread == "clinic":
            # Get or create clinic-wide thread
            thread = _get_or_create_clinic_thread(db, dados.clinica_id)
        elif dados.tipo_thread == "dm":
            # Get or create DM thread
            if not dados.destinatario_id:
                raise ValueError("destinatario_id obrigatório para DM.")
            thread = _get_or_create_thread(
                db, remetente.id, dados.destinatario_id, dados.clinica_id
            )
        else:
            raise ValueError("Tipo de thread inválido.")

    # Create the message
    msg = models.Mensagem(
        clinica_id=dados.clinica_id,
        thread_id=thread.id,
        remetente_id=remetente.id,
        texto=dados.texto,
        created_at=datetime.utcnow(),
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def listar_mensagens(db: Session, thread_id: int, clinica_id: int, limit: int = 30, before_id: Optional[int] = None):
    """List messages for a thread with user information."""
    query = (
        db.query(models.Mensagem)
        .filter(models.Mensagem.thread_id == thread_id)
        .filter(models.Mensagem.clinica_id == clinica_id)
        .order_by(models.Mensagem.created_at.desc())
    )
    
    if before_id:
        query = query.filter(models.Mensagem.id < before_id)
    
    messages = query.limit(limit).all()
    
    # Get user information for each message
    result = []
    for msg in messages:
        # Get user name from Utilizador table
        user = db.query(Utilizador).filter(Utilizador.id == msg.remetente_id).first()
        
        # Create a dictionary with message data plus user name
        msg_dict = {
            "id": msg.id,
            "thread_id": msg.thread_id,
            "remetente_id": msg.remetente_id,
            "remetente_nome": user.nome if user else None,
            "clinica_id": msg.clinica_id,
            "texto": msg.texto,
            "created_at": msg.created_at,
            "lida": msg.lida
        }
        result.append(msg_dict)
    
    return result


def listar_threads(db: Session, user_id: int, clinica_id: int):
    threads = (
        db.query(models.Thread)
          .options(joinedload(models.Thread.mensagens))
          .filter(
              models.Thread.clinica_id == clinica_id,
              or_(
                  models.Thread.participante_a_id == user_id,
                  models.Thread.participante_b_id == user_id,
              )
          )
          .all()
    )
    out = []
    for t in threads:
        outro = (
            t.participante_a_id
            if t.participante_b_id == user_id
            else t.participante_b_id
        )
        ultima = t.mensagens[-1] if t.mensagens else None
        out.append(
            {
                "id": t.id,
                "clinica_id": clinica_id,
                "outro_participante_id": outro,
                "ultima_mensagem": ultima,
            }
        )
    return out


def _get_or_create_clinic_thread(
    db: Session,
    clinica_id: int
) -> models.Thread:
    """Get or create a clinic-wide thread for all users in a clinic."""
    thread = (
        db.query(models.Thread)
          .filter_by(
              clinica_id=clinica_id,
              tipo="clinic",
              participante_a_id=None,
              participante_b_id=None
          )
          .first()
    )
    if thread:
        return thread

    thread = models.Thread(
        clinica_id=clinica_id,
        nome=f"Clínica Geral",
        tipo="clinic",
        created_at=datetime.utcnow()
    )
    db.add(thread)
    db.commit()
    db.refresh(thread)
    return thread