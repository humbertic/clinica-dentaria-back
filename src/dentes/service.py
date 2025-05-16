from sqlalchemy.orm import Session
from . import models


def listar_dentes(db: Session):
    """Retorna todos os dentes cadastrados no sistema."""
    return db.query(models.Dente).order_by(models.Dente.id).all()


def obter_dente_por_id(db: Session, dente_id: int):
    """Busca um dente pelo seu ID."""
    return db.query(models.Dente).filter(models.Dente.id == dente_id).first()


def listar_dentes_por_tipo(db: Session, tipo: str):
    """Retorna todos os dentes de um determinado tipo (permanente ou decíduo)."""
    return db.query(models.Dente).filter(models.Dente.tipo == tipo).all()


def listar_dentes_por_arcada(db: Session, arcada: str):
    """Retorna todos os dentes de uma determinada arcada (superior ou inferior)."""
    return db.query(models.Dente).filter(models.Dente.arcada == arcada).all()


def listar_faces(db: Session):
    """Retorna todas as faces dentárias cadastradas no sistema."""
    return db.query(models.Face).all()