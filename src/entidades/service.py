from sqlalchemy.orm import Session
from src.utilizadores.models import Utilizador
from src.utilizadores.utils import is_master_admin
from src.auditoria.utils import registrar_auditoria
from src.entidades import models, schemas

def listar_entidades(db: Session):
    return db.query(models.Entidade).order_by(models.Entidade.nome).all()

def obter_entidade_por_id(db: Session, entidade_id: int):
    return db.query(models.Entidade).filter_by(id=entidade_id).first()

def criar_entidade(db: Session, dados: schemas.EntidadeCreate, user: Utilizador):
    ent = models.Entidade(**dados.dict())
    db.add(ent)
    db.commit()
    db.refresh(ent)
    registrar_auditoria(
        db, user.id, "Criação", "Entidade", ent.id,
        f"Entidade '{ent.nome}' criada."
    )
    return ent

def atualizar_entidade(db: Session, entidade_id: int, dados: schemas.EntidadeUpdate, user: Utilizador):
    ent = db.query(models.Entidade).filter_by(id=entidade_id).first()
    if not ent:
        return None
    for k, v in dados.dict().items():
        setattr(ent, k, v)
    db.commit()
    db.refresh(ent)
    registrar_auditoria(
        db, user.id, "Atualização", "Entidade", ent.id,
        f"Entidade '{ent.nome}' atualizada."
    )
    return ent

def remover_entidade(db: Session, entidade_id: int, user: Utilizador):
    ent = db.query(models.Entidade).filter_by(id=entidade_id).first()
    if ent:
        db.delete(ent)
        db.commit()
        registrar_auditoria(
            db, user.id, "Remoção", "Entidade", entidade_id,
            f"Entidade '{ent.nome}' removida."
        )
    return ent
