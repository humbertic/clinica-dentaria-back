from pydantic import BaseModel

class EntidadeBase(BaseModel):
    slug: str
    nome: str

class EntidadeCreate(EntidadeBase):
    pass

class EntidadeUpdate(EntidadeBase):
    pass

class EntidadeResponse(EntidadeBase):
    id: int

    class Config:
        orm_mode = True
