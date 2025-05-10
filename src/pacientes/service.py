from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, selectinload

from src.pacientes import models, schemas
from src.auditoria.utils import registrar_auditoria



# -------------------------------------------------
# --------- PACIENTE ------------------------------
# -------------------------------------------------
def criar_paciente(
    db: Session,
    dados: schemas.PacienteCreate,
    utilizador_id: int
) -> models.Paciente:
    if dados.telefone and db.query(models.Paciente).filter_by(telefone=dados.telefone).first():
        raise HTTPException(status_code=400, detail="Telefone já registado.")
    if dados.email and db.query(models.Paciente).filter_by(email=dados.email).first():
        raise HTTPException(status_code=400, detail="E-mail já registado.")
    if dados.nif and db.query(models.Paciente).filter_by(nif=dados.nif).first():
        raise HTTPException(status_code=400, detail="NIF já registado.")

    paciente = models.Paciente(**dados.dict())
    db.add(paciente)
    db.commit()
    db.refresh(paciente)

    registrar_auditoria(
        db,
        utilizador_id,
        "Criação",
        "Paciente",
        paciente.id,
        f"Paciente '{paciente.nome}' criado."
    )
    return paciente


def listar_pacientes(db: Session, clinica_id: int):
    return (
        db.query(models.Paciente)
          .options(selectinload(models.Paciente.clinica))
          .filter_by(clinica_id=clinica_id)
          .order_by(models.Paciente.nome)
          .all()
    )


def obter_paciente(db: Session, paciente_id: int) -> models.Paciente:
    paciente = db.query(models.Paciente).filter_by(id=paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente não encontrado.")
    return paciente


def atualizar_paciente(
    db: Session,
    paciente_id: int,
    dados: schemas.PacienteUpdate,
    utilizador_id: int
) -> models.Paciente:
    paciente = obter_paciente(db, paciente_id)

    for campo, valor in dados.dict(exclude_unset=True).items():
        setattr(paciente, campo, valor)

    db.commit()
    db.refresh(paciente)

    registrar_auditoria(
        db,
        utilizador_id,
        "Atualização",
        "Paciente",
        paciente_id,
        f"Paciente '{paciente.nome}' atualizado."
    )
    return paciente


# -------------------------------------------------
# --------- FICHA CLÍNICA -------------------------
# -------------------------------------------------
def criar_ficha_clinica(
    db: Session,
    dados: schemas.FichaClinicaCreate,
    utilizador_id: int
) -> models.FichaClinica:
    ficha = models.FichaClinica(**dados.dict(), responsavel_criacao_id=utilizador_id)
    db.add(ficha)
    db.commit()
    db.refresh(ficha)

    registrar_auditoria(
        db,
        utilizador_id,
        "Criação",
        "FichaClinica",
        ficha.id,
        f"Ficha clínica criada para paciente {ficha.paciente_id}."
    )
    return ficha


def obter_ficha(db: Session, ficha_id: int) -> models.FichaClinica:
    """
    Recupera uma ficha clínica pelo seu ID.
    Levanta 404 se não existir.
    """
    ficha = (
        db.query(models.FichaClinica)
          .options(
              selectinload(models.FichaClinica.paciente),
              selectinload(models.FichaClinica.anotacoes),
              selectinload(models.FichaClinica.ficheiros),
          )
          .filter(models.FichaClinica.id == ficha_id)
          .first()
    )
    if not ficha:
        raise HTTPException(status_code=404, detail="Ficha clínica não encontrada.")
    return ficha


def atualizar_ficha_clinica(
    db: Session,
    ficha_id: int,
    dados: schemas.FichaClinicaUpdate,
    utilizador_id: int
) -> models.FichaClinica:
    """
    Atualiza os campos de uma ficha clínica existente.
    Só altera os campos definidos em dados.
    Regista auditoria do update.
    """
    ficha = db.query(models.FichaClinica).filter_by(id=ficha_id).first()
    if not ficha:
        raise HTTPException(status_code=404, detail="Ficha clínica não encontrada.")

    # aplica apenas os campos enviados
    for campo, valor in dados.dict(exclude_unset=True).items():
        setattr(ficha, campo, valor)

    # atualiza quem e quando
    ficha.responsavel_atualizacao_id = utilizador_id

    db.commit()
    db.refresh(ficha)

    registrar_auditoria(
        db,
        utilizador_id,
        "Atualização",
        "FichaClinica",
        ficha.id,
        f"Ficha clínica {ficha.id} atualizada."
    )
    return ficha


def adicionar_anotacao(
    db: Session,
    dados: schemas.AnotacaoClinicaCreate,
    utilizador_id: int
) -> models.AnotacaoClinica:
    # verifica se ficha existe
    ficha = db.query(models.FichaClinica).filter_by(id=dados.ficha_id).first()
    if not ficha:
        raise HTTPException(status_code=404, detail="Ficha clínica não encontrada.")

    anot = models.AnotacaoClinica(**dados.dict())
    db.add(anot)
    db.commit()
    db.refresh(anot)

    registrar_auditoria(
        db,
        utilizador_id,
        "Criação",
        "AnotacaoClinica",
        anot.id,
        f"Anotação adicionada à ficha {dados.ficha_id}."
    )
    return anot


def upload_ficheiro_clinico(
    db: Session,
    dados: schemas.FicheiroClinicoCreate,
    utilizador_id: int
) -> models.FicheiroClinico:
    ficheiro = models.FicheiroClinico(**dados.dict())
    db.add(ficheiro)
    db.commit()
    db.refresh(ficheiro)

    registrar_auditoria(
        db,
        utilizador_id,
        "Upload",
        "FicheiroClinico",
        ficheiro.id,
        f"Ficheiro '{ficheiro.tipo}' anexado à ficha {dados.ficha_id}."
    )
    return ficheiro


# -------------------------------------------------
# --------- PLANO DE TRATAMENTO -------------------
# -------------------------------------------------
def criar_plano(
    db: Session,
    dados: schemas.PlanoTratamentoCreate,
    utilizador_id: int
) -> models.PlanoTratamento:
    plano = models.PlanoTratamento(**dados.dict(), estado="em_curso")
    db.add(plano)
    db.commit()
    db.refresh(plano)

    registrar_auditoria(
        db,
        utilizador_id,
        "Criação",
        "PlanoTratamento",
        plano.id,
        f"Plano de tratamento criado para paciente {plano.paciente_id}."
    )
    return plano


def atualizar_plano(
    db: Session,
    plano_id: int,
    dados: schemas.PlanoTratamentoUpdate,
    utilizador_id: int
) -> models.PlanoTratamento:
    plano = db.query(models.PlanoTratamento).filter_by(id=plano_id).first()
    if not plano:
        raise HTTPException(status_code=404, detail="Plano não encontrado.")

    for campo, valor in dados.dict(exclude_unset=True).items():
        setattr(plano, campo, valor)

    db.commit()
    db.refresh(plano)

    registrar_auditoria(
        db,
        utilizador_id,
        "Atualização",
        "PlanoTratamento",
        plano_id,
        f"Plano de tratamento {plano_id} atualizado."
    )
    return plano
