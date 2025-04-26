from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from src.perfis import models, schemas
from fastapi import HTTPException

def criar_perfil(db: Session, dados: schemas.PerfilCreate) -> models.Perfil:
    perfil = models.Perfil(nome=dados.nome)
    db.add(perfil)
    try:
        db.commit()
        db.refresh(perfil)
        return perfil
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Já existe um perfil com esse nome.")

def atualizar_perfil(db: Session, perfil_id: int, dados: schemas.PerfilUpdate) -> models.Perfil:
    perfil = db.query(models.Perfil).filter_by(id=perfil_id).first()
    if not perfil:
        raise HTTPException(status_code=404, detail="Perfil não encontrado")
    perfil.nome = dados.nome
    try:
        db.commit()
        db.refresh(perfil)
        return perfil
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Já existe um perfil com esse nome.")

def listar_perfis(db: Session):
    return db.query(models.Perfil).all()


