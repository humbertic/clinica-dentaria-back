from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import func

from src.auditoria.utils import registrar_auditoria
from . import models, schemas


def get_quantidade_atual(db: Session, item_id: int) -> int:
    total = db.query(func.sum(models.ItemLote.quantidade)).filter_by(item_id=item_id).scalar()
    return total or 0

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
    item = db.query(models.ItemStock).filter_by(id=item_id).first()
    if not item:
        return None
    quantidade_atual = get_quantidade_atual(db, item.id)
    lotes = [schemas.ItemLoteResponse.model_validate(lote) for lote in item.lotes]
    proximo_lote = get_proximo_lote(db, item.id)
    return {
        "id": item.id,
        "clinica_id": item.clinica_id,
        "nome": item.nome,
        "descricao": item.descricao,
        "quantidade_minima": item.quantidade_minima,
        "tipo_medida": item.tipo_medida,
        "fornecedor": item.fornecedor,
        "ativo": item.ativo,
        "quantidade_atual": quantidade_atual,
        "lote_proximo": proximo_lote.lote if proximo_lote else None,
        "validade_proxima": proximo_lote.validade if proximo_lote else None,
        "lotes": lotes
    }

def listar_itens_stock(db: Session, clinica_id: int):
    itens = db.query(models.ItemStock).filter_by(clinica_id=clinica_id).all()
    result = []
    for item in itens:
        quantidade_atual = get_quantidade_atual(db, item.id)
        lotes = [schemas.ItemLoteResponse.model_validate(lote) for lote in item.lotes]
        proximo_lote = get_proximo_lote(db, item.id)
        result.append({
            "id": item.id,
            "clinica_id": item.clinica_id,
            "nome": item.nome,
            "descricao": item.descricao,
            "quantidade_minima": item.quantidade_minima,
            "tipo_medida": item.tipo_medida,
            "fornecedor": item.fornecedor,
            "ativo": item.ativo,
            "quantidade_atual": quantidade_atual,
            "lote_proximo": proximo_lote.lote if proximo_lote else None,
            "validade_proxima": proximo_lote.validade if proximo_lote else None,
            "lotes": lotes
        })
    return result

def atualizar_item_stock(db: Session, item_id: int, item: schemas.ItemStockUpdate, user_id: int):
    db_item = db.query(models.ItemStock).filter_by(id=item_id).first()
    if not db_item:
        return None
    update_data = item.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_item, key, value)
    db.commit()
    db.refresh(db_item)
    registrar_auditoria(
        db, user_id, "Atualização", "ItemStock", db_item.id, f"Item '{db_item.nome}' atualizado no estoque."
    )
    return db_item

# --------- MOVIMENTO STOCK ---------
def criar_movimento_stock(db: Session, movimento: schemas.MovimentoStockCreate):
    item = db.query(models.ItemStock).filter_by(id=movimento.item_id).first()
    if not item:
        raise ValueError("Item de estoque não encontrado.")

    if movimento.tipo_movimento == "entrada":
        if not movimento.lote or not movimento.validade:
            raise ValueError("Lote e validade são obrigatórios para entrada de estoque.")
        entrada_lote(
            db,
            item_id=movimento.item_id,
            lote=movimento.lote,
            validade=movimento.validade,
            quantidade=movimento.quantidade
        )
    elif movimento.tipo_movimento in ["saida", "ajuste"]:
        saida_lote(
            db,
            item_id=movimento.item_id,
            quantidade=movimento.quantidade
        )
    elif movimento.tipo_movimento == "transferencia":
        transferencia(db, movimento, item)
    else:
        raise ValueError("Tipo de movimento inválido.")

    mov_dict = movimento.dict(exclude={"lote", "validade","destino_id"})
    db_mov = models.MovimentoStock(**mov_dict)
    db.add(db_mov)
    db.commit()
    db.refresh(db_mov)
    db.refresh(item)

    registrar_auditoria(
        db,
        movimento.utilizador_id,
        movimento.tipo_movimento.capitalize(),
        "MovimentoStock",
        db_mov.id,
        f"Movimento '{movimento.tipo_movimento}' de {movimento.quantidade} no item '{item.nome}' (ID {item.id}). Justificação: {movimento.justificacao or 'N/A'}"
    )
    return db_mov

def listar_movimentos_stock(db: Session, item_id: int):
    movimentos = db.query(models.MovimentoStock).filter_by(item_id=item_id).all()
    result = []
    for mov in movimentos:
        utilizador = mov.utilizador
        result.append({
            "id": mov.id,
            "item_id": mov.item_id,
            "tipo_movimento": mov.tipo_movimento,
            "quantidade": mov.quantidade,
            "data": mov.data,
            "justificacao": mov.justificacao,
            "utilizador": {
                "id": utilizador.id,
                "nome": utilizador.nome,
            } if utilizador else None,
        })
    return result

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

# --------- LOTES ---------
def entrada_lote(db: Session, item_id: int, lote: str, validade: date, quantidade: int):
    lote = lote.upper()
    item_lote = db.query(models.ItemLote).filter_by(item_id=item_id, lote=lote, validade=validade).first()
    if item_lote:
        item_lote.quantidade += quantidade
    else:
        item_lote = models.ItemLote(item_id=item_id, lote=lote, validade=validade, quantidade=quantidade)
        db.add(item_lote)
    db.commit()
    db.refresh(item_lote)
    return item_lote

def saida_lote(db: Session, item_id: int, quantidade: int):
    lotes = db.query(models.ItemLote).filter_by(item_id=item_id).order_by(models.ItemLote.validade).all()
    restante = quantidade
    for lote in lotes:
        if lote.quantidade >= restante:
            lote.quantidade -= restante
            restante = 0
            db.commit()
            db.refresh(lote)
            break
        else:
            restante -= lote.quantidade
            lote.quantidade = 0
            db.commit()
            db.refresh(lote)
    if restante > 0:
        raise ValueError("Estoque insuficiente nos lotes para a saída solicitada.")
    return True

def transferencia(db: Session, movimento: schemas.MovimentoStockCreate, item):
    if not movimento.destino_id:
        raise ValueError("Destino da transferência não informado.")
    lotes_origem = db.query(models.ItemLote).filter_by(item_id=movimento.item_id).order_by(models.ItemLote.validade).all()
    restante = movimento.quantidade
    lotes_transferidos = []
    for lote in lotes_origem:
        if restante <= 0:
            break
        transferir = min(lote.quantidade, restante)
        lote.quantidade -= transferir
        lote_nome_upper = lote.lote.upper()
        lote.lote = lote_nome_upper
        lotes_transferidos.append((lote_nome_upper, lote.validade, transferir))
        # Registra movimento de saída para cada lote
        registrar_movimento_saida(db, item.id, transferir, movimento.utilizador_id, movimento.justificacao or "Transferência", lote.lote, lote.validade)
        restante -= transferir
        db.commit()
        db.refresh(lote)
    if restante > 0:
        raise ValueError("Estoque insuficiente para transferência.")

    item_destino = db.query(models.ItemStock).filter_by(nome=item.nome, clinica_id=movimento.destino_id).first()
    if not item_destino:
        item_destino = models.ItemStock(
            nome=item.nome,
            descricao=item.descricao,
            quantidade_minima=item.quantidade_minima,
            tipo_medida=item.tipo_medida,
            fornecedor=item.fornecedor,
            ativo=item.ativo,
            clinica_id=movimento.destino_id
        )
        db.add(item_destino)
        db.commit()
        db.refresh(item_destino)

    for lote_nome, validade, qtd in lotes_transferidos:
        lote_nome = lote_nome.upper()
        lote_destino = db.query(models.ItemLote).filter_by(item_id=item_destino.id, lote=lote_nome, validade=validade).first()
        if lote_destino:
            lote_destino.quantidade += qtd
        else:
            lote_destino = models.ItemLote(item_id=item_destino.id, lote=lote_nome, validade=validade, quantidade=qtd)
            db.add(lote_destino)
        db.commit()
        db.refresh(lote_destino)
        # Registra movimento de entrada para cada lote
        registrar_movimento_entrada(db, item_destino.id, qtd, movimento.utilizador_id, movimento.justificacao or "Transferência", lote_nome, validade)
        
def registrar_movimento_entrada(db: Session, item_id: int, quantidade: int, user_id: int, justificacao: str, lote: str, validade: date):
    mov_entrada = models.MovimentoStock(
        item_id=item_id,
        tipo_movimento="entrada",
        quantidade=quantidade,
        utilizador_id=user_id,
        justificacao=justificacao,
       
    )
    db.add(mov_entrada)
    db.commit()
    db.refresh(mov_entrada)
    return mov_entrada

def registrar_movimento_saida(db: Session, item_id: int, quantidade: int, user_id: int, justificacao: str, lote: str, validade: date):
    mov_saida = models.MovimentoStock(
        item_id=item_id,
        tipo_movimento="saida",
        quantidade=quantidade,
        utilizador_id=user_id,
        justificacao=justificacao,
    )
    db.add(mov_saida)
    db.commit()
    db.refresh(mov_saida)
    return mov_saida

def get_proximo_lote(db: Session, item_id: int):
    return db.query(models.ItemLote).filter_by(item_id=item_id).order_by(models.ItemLote.validade).first()