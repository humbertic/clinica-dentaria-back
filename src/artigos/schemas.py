from pydantic import BaseModel
from typing import Optional, List
from src.categoria.schemas import CategoriaResponse
from src.precos.schemas import PrecoResponse

class ArtigoBase(BaseModel):
    codigo: str
    descricao: str
    categoria_id: int

class ArtigoCreate(ArtigoBase):
    pass

class ArtigoUpdate(BaseModel):
    codigo: Optional[str]
    descricao: Optional[str]
    categoria_id: Optional[int]

class ArtigoResponse(BaseModel):
    id: int
    codigo: str
    descricao: str
    categoria: CategoriaResponse
    precos: List[PrecoResponse] = []

    class Config:
        orm_mode = True