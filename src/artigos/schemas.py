from pydantic import BaseModel
from typing import Optional, List
from src.categoria.schemas import CategoriaResponse
from src.precos.schemas import PrecoResponse

class ArtigoBase(BaseModel):
    codigo: str
    descricao: str
    categoria_id: int
    requer_dente: bool = False
    requer_face: bool = False
    face_count: Optional[int] = None

class ArtigoCreate(ArtigoBase):
    pass

class ArtigoUpdate(BaseModel):
    codigo: Optional[str] = None
    descricao: Optional[str] = None
    categoria_id: Optional[int] = None
    requer_dente: Optional[bool] = None
    requer_face: Optional[bool] = None
    face_count: Optional[int] = None

class ArtigoResponse(BaseModel):
    id: int
    codigo: str
    descricao: str
    categoria: CategoriaResponse
    precos: List[PrecoResponse] = []
    requer_dente: bool
    requer_face: bool
    face_count: Optional[int] = None

    class Config:
        orm_mode = True
        
        
class ArtigoMinimal(BaseModel):
    id: int
    codigo: str
    descricao: str
    face_count: Optional[int] = None
    
    class Config:
        orm_mode = True