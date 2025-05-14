from sqlalchemy.orm import Session
from src.precos.models import Preco
from src.precos.schemas import PrecoCreate, PrecoUpdate
from src.auditoria.utils import registrar_auditoria


def criar_preco(db: Session, dados: PrecoCreate, criado_por: int) -> Preco:
    preco = Preco(**dados.dict())
    db.add(preco)
    db.commit()
    db.refresh(preco)
    registrar_auditoria(
        db,
        criado_por,
        "Criação",
        "Preço",
        preco.artigo_id,
        f"Preço para artigo {preco.artigo_id} e entidade {preco.entidade_id} criado: {preco.valor_entidade}."
    )
    return preco


def listar_precos(db: Session):
    return db.query(Preco).all()


def obter_preco(db: Session, artigo_id: int, entidade_id: int):
    return (
        db.query(Preco)
          .filter(Preco.artigo_id == artigo_id, Preco.entidade_id == entidade_id)
          .first()
    )


def atualizar_preco(
    db: Session,
    artigo_id: int,
    entidade_id: int,
    dados: PrecoUpdate,
    atualizado_por: int
) -> Preco | None:
    preco = obter_preco(db, artigo_id, entidade_id)
    if not preco:
        return None
    preco.valor_entidade = dados.valor_entidade
    preco.valor_paciente = dados.valor_paciente
    db.commit()
    db.refresh(preco)
    registrar_auditoria(
        db,
        atualizado_por,
        "Atualização",
        "Preço",
        artigo_id,
        f"Preço para artigo {artigo_id} e entidade {entidade_id} atualizado para {preco.valor_entidade}."
    )
    return preco


def remover_preco(
    db: Session,
    artigo_id: int,
    entidade_id: int,
    removido_por: int
) -> bool:
    preco = obter_preco(db, artigo_id, entidade_id)
    if not preco:
        return False
    db.delete(preco)
    db.commit()
    registrar_auditoria(
        db,
        removido_por,
        "Remoção",
        "Preço",
        artigo_id,
        f"Preço para artigo {artigo_id} e entidade {entidade_id} removido."
    )
    return True