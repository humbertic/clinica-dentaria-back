from pydantic import BaseModel
from typing import Optional

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

class ArtigoResponse(ArtigoBase):
    id: int

    class Config:
        orm_mode = True