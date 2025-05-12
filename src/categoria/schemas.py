from pydantic import BaseModel
from typing import Optional


class CategoriaBase(BaseModel):
    slug: str
    nome: str
    ordem: int = 0

class CategoriaCreate(CategoriaBase):
    pass

class CategoriaUpdate(BaseModel):
    slug: Optional[str]
    nome: Optional[str]
    ordem: Optional[int]

class CategoriaResponse(CategoriaBase):
    id: int

    class Config:
        orm_mode = True
