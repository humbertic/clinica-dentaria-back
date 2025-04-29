from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database import SessionLocal
from . import service, schemas
from src.utilizadores.dependencies import get_current_user

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
def check_permission(user, allowed_perfis, clinica_id=None):
    for uc in user.perfis:
        if clinica_id is None or uc.clinica_id == clinica_id:
            if uc.perfil.perfil in allowed_perfis:
                return True
    raise HTTPException(status_code=403, detail="Operação não permitida para este perfil.")

@router.post("/items", response_model=schemas.ItemStockResponse)
def criar_item(
    item: schemas.ItemStockCreate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    check_permission(user, ["master_admin", "gerente"])
    return service.criar_item_stock(db, item, user.id)

@router.get("/items/{clinica_id}", response_model=list[schemas.ItemStockResponse])
def listar_itens(
    clinica_id: int,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)  
):
    return service.listar_itens_stock(db, clinica_id)

@router.get("/item/{item_id}", response_model=schemas.ItemStockResponse)
def obter_item_por_id(
    item_id: int,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    item = service.obter_item_stock_por_id(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    return item

@router.put("/items/{item_id}", response_model=schemas.ItemStockResponse)
def atualizar_item(
    item_id: int,
    item: schemas.ItemStockUpdate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    check_permission(user, ["master_admin", "gerente"])
    db_item = service.atualizar_item_stock(db, item_id, item, user.id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    return service.obter_item_stock_por_id(db, item_id)

# --------- MOVIMENTO STOCK ---------
@router.post("/movimentos", response_model=schemas.MovimentoStockResponse)
def criar_movimento(
    movimento: schemas.MovimentoStockCreate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)  
):
    return service.criar_movimento_stock(db, movimento)


@router.get("/movimentos/{item_id}", response_model=list[schemas.MovimentoStockResponse])
def listar_movimentos(
    item_id: int,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)  
):
    return service.listar_movimentos_stock(db, item_id)

# --------- ITEM FILIAL ---------
@router.put("/itemfilial", response_model=schemas.ItemFilialResponse)
def atualizar_item_filial(
    item_id: int,
    filial_id: int,
    quantidade: int,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    return service.atualizar_item_filial(db, item_id, filial_id, quantidade)

@router.get("/itemfilial/{item_id}", response_model=list[schemas.ItemFilialResponse])
def listar_item_filial(
    item_id: int,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    return service.listar_item_filial(db, item_id)