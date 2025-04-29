from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime

class ItemLoteBase(BaseModel):
    lote: str
    validade: date
    quantidade: int

class ItemLoteCreate(ItemLoteBase):
    item_id: int

class ItemLoteResponse(ItemLoteBase):
    id: int
    item_id: int

    model_config = {"from_attributes": True}

class UtilizadorResumo(BaseModel):
    id: int
    nome: str

    class Config:
        orm_mode = True

class ItemStockBase(BaseModel):
    nome: str
    descricao: Optional[str] = None
    quantidade_minima: int
    tipo_medida: str
    fornecedor: Optional[str] = None
    ativo: Optional[bool] = True

class ItemStockCreate(ItemStockBase):
    clinica_id: int
    
class ItemStockUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    quantidade_minima: Optional[int] = None
    tipo_medida: Optional[str] = None
    fornecedor: Optional[str] = None
    ativo: Optional[bool] = None
    
    class Config:
        orm_mode = True

class ItemStockResponse(ItemStockBase):
    id: int
    clinica_id: int
    quantidade_atual: Optional[int] = None
    lote_proximo: Optional[str] = None
    validade_proxima: Optional[date] = None
    lotes: Optional[List[ItemLoteResponse]] = None

    class Config:
        orm_mode = True

class MovimentoStockBase(BaseModel):
    item_id: int
    tipo_movimento: str
    quantidade: int
    justificacao: Optional[str] = None
    lote: Optional[str] = None         
    validade: Optional[date] = None  
    destino_id: Optional[int] = None  

class MovimentoStockCreate(MovimentoStockBase):
    utilizador_id: int

class MovimentoStockResponse(MovimentoStockBase):
    id: int
    data: Optional[datetime]
    utilizador: Optional[UtilizadorResumo] = None

    class Config:
        orm_mode = True

class ItemFilialBase(BaseModel):
    item_id: int
    filial_id: int
    quantidade: int

class ItemFilialResponse(ItemFilialBase):
    class Config:
        orm_mode = True