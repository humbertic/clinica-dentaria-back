from pydantic import BaseModel
from typing import Optional
from datetime import date

class ItemStockBase(BaseModel):
    nome: str
    descricao: Optional[str] = None
    lote: Optional[str] = None
    quantidade_atual: int
    quantidade_minima: int
    validade: Optional[date] = None
    tipo_medida: str
    fornecedor: Optional[str] = None
    ativo: Optional[bool] = True

class ItemStockCreate(ItemStockBase):
    clinica_id: int

class ItemStockResponse(ItemStockBase):
    id: int
    clinica_id: int

    class Config:
        orm_mode = True

class MovimentoStockBase(BaseModel):
    item_id: int
    tipo_movimento: str
    quantidade: int
    justificacao: Optional[str] = None

class MovimentoStockCreate(MovimentoStockBase):
    utilizador_id: int

class MovimentoStockResponse(MovimentoStockBase):
    id: int
    data: Optional[date]
    utilizador_id: int

    class Config:
        orm_mode = True

class ItemFilialBase(BaseModel):
    item_id: int
    filial_id: int
    quantidade: int

class ItemFilialResponse(ItemFilialBase):
    class Config:
        orm_mode = True