from sqlalchemy.orm import Session
from src.categoria.models import Categoria
from src.categoria.schemas import CategoriaCreate, CategoriaUpdate
from src.auditoria.utils import registrar_auditoria

def criar_categoria(db: Session, dados: CategoriaCreate, criado_por_id: int) -> Categoria:
    cat = Categoria(**dados.dict())
    db.add(cat)
    db.commit()
    db.refresh(cat)
    registrar_auditoria(
        db,
        criado_por_id,
        "Criação",
        "Categoria",
        cat.id,
        f"Categoria '{cat.nome}' criada."
    )
    return cat

def listar_categorias(db: Session):
    return db.query(Categoria).order_by(Categoria.ordem).all()

def obter_categoria_por_id(db: Session, categoria_id: int):
    return db.query(Categoria).filter(Categoria.id == categoria_id).first()

def atualizar_categoria(
    db: Session,
    categoria_id: int,
    dados: CategoriaUpdate,
    atualizado_por_id: int
):
    cat = db.query(Categoria).filter(Categoria.id == categoria_id).first()
    if not cat:
        return None
    for key, value in dados.dict(exclude_unset=True).items():
        setattr(cat, key, value)
    db.commit()
    db.refresh(cat)
    registrar_auditoria(
        db,
        atualizado_por_id,
        "Atualização",
        "Categoria",
        cat.id,
        f"Categoria '{cat.nome}' atualizada."
    )
    return cat

def remover_categoria(db: Session, categoria_id: int, removido_por_id: int) -> bool:
    cat = db.query(Categoria).filter(Categoria.id == categoria_id).first()
    if not cat:
        return False
    db.delete(cat)
    db.commit()
    registrar_auditoria(
        db,
        removido_por_id,
        "Remoção",
        "Categoria",
        categoria_id,
        f"Categoria '{cat.nome}' removida."
    )
    return True
