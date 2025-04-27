from sqlalchemy.orm import Session

from src.auditoria.utils import registrar_auditoria
from . import models, schemas

"""
Todo:
- [ ] Implementar validações e regras de negócio.
- [ ] Implementar dedução automática de stock.
- [ ] Implementar alertas automáticos.
- [ ] Implementar endpoint para consulta de alertas.
- [ ] Implementar transferência entre filiais.
- [ ] Implementar justificativa obrigatória para ajustes manuais.
- [ ] Implementar transacionalidade nas operações críticas.
"""

# --------- ITEM STOCK ---------
def criar_item_stock(db: Session, item: schemas.ItemStockCreate, user_id: int):
    db_item = models.ItemStock(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    registrar_auditoria(
        db, user_id, "Criação", "ItemStock", db_item.id, f"Item '{db_item.nome}' criado no estoque."
    )
    return db_item

def obter_item_stock_por_id(db: Session, item_id: int):
    return db.query(models.ItemStock).filter_by(id=item_id).first()

def listar_itens_stock(db: Session, clinica_id: int):
    return db.query(models.ItemStock).filter_by(clinica_id=clinica_id).all()

def atualizar_item_stock(db: Session, item_id: int, item: schemas.ItemStockCreate):
    db_item = db.query(models.ItemStock).filter_by(id=item_id).first()
    if not db_item:
        return None
    for key, value in item.dict().items():
        setattr(db_item, key, value)
    db.commit()
    db.refresh(db_item)
    registrar_auditoria(
        db, item_id, "Atualização", "ItemStock", db_item.id, f"Item '{db_item.nome}' atualizado no estoque."
    )
    return db_item

# --------- MOVIMENTO STOCK ---------
def criar_movimento_stock(db: Session, movimento: schemas.MovimentoStockCreate):
    db_mov = models.MovimentoStock(**movimento.dict())
    db.add(db_mov)
    db.commit()
    db.refresh(db_mov)
    return db_mov

def listar_movimentos_stock(db: Session, item_id: int):
    return db.query(models.MovimentoStock).filter_by(item_id=item_id).all()

# --------- ITEM FILIAL ---------
def atualizar_item_filial(db: Session, item_id: int, filial_id: int, quantidade: int):
    db_item_filial = db.query(models.ItemFilial).filter_by(item_id=item_id, filial_id=filial_id).first()
    if db_item_filial:
        db_item_filial.quantidade = quantidade
    else:
        db_item_filial = models.ItemFilial(item_id=item_id, filial_id=filial_id, quantidade=quantidade)
        db.add(db_item_filial)
    db.commit()
    return db_item_filial

def listar_item_filial(db: Session, item_id: int):
    return db.query(models.ItemFilial).filter_by(item_id=item_id).all()