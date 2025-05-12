from sqlalchemy.orm import Session
from src.artigos.models import ArtigoMedico
from src.artigos.schemas import ArtigoCreate, ArtigoUpdate
from src.auditoria.utils import registrar_auditoria
from sqlalchemy.orm import joinedload


def criar_artigo(db: Session, dados: ArtigoCreate, criado_por_id: int) -> ArtigoMedico:
    artigo = ArtigoMedico(**dados.dict())
    db.add(artigo)
    db.commit()
    db.refresh(artigo)
    registrar_auditoria(
        db,
        criado_por_id,
        "Criação",
        "ArtigoMedico",
        artigo.id,
        f"Artigo '{artigo.codigo}' criado."
    )
    return artigo


def listar_artigos(db: Session):
    return (
        db.query(ArtigoMedico)
        .options(
            joinedload(ArtigoMedico.categoria),
        )
        .order_by(ArtigoMedico.id)
        .all()
    )

def obter_artigo_por_id(db: Session, artigo_id: int):
    return db.query(ArtigoMedico).filter(ArtigoMedico.id == artigo_id).first()


def atualizar_artigo(
    db: Session,
    artigo_id: int,
    dados: ArtigoUpdate,
    atualizado_por_id: int
):
    artigo = db.query(ArtigoMedico).filter(ArtigoMedico.id == artigo_id).first()
    if not artigo:
        return None
    for key, value in dados.dict(exclude_unset=True).items():
        setattr(artigo, key, value)
    db.commit()
    db.refresh(artigo)
    registrar_auditoria(
        db,
        atualizado_por_id,
        "Atualização",
        "ArtigoMedico",
        artigo.id,
        f"Artigo '{artigo.codigo}' atualizado."
    )
    return artigo


def remover_artigo(db: Session, artigo_id: int, removido_por_id: int) -> bool:
    artigo = db.query(ArtigoMedico).filter(ArtigoMedico.id == artigo_id).first()
    if not artigo:
        return False
    db.delete(artigo)
    db.commit()
    registrar_auditoria(
        db,
        removido_por_id,
        "Remoção",
        "ArtigoMedico",
        artigo_id,
        f"Artigo '{artigo.codigo}' removido."
    )
    return True