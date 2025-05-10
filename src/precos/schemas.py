from pydantic import BaseModel
from decimal import Decimal
from typing import Optional

class PrecoBase(BaseModel):
    artigo_id: int
    entidade_id: int
    valor_entidade: Decimal
    valor_paciente: Decimal

class PrecoCreate(PrecoBase):
    pass

class PrecoUpdate(BaseModel):
    valor_entidade: Decimal
    valor_paciente: Decimal

class PrecoResponse(PrecoBase):
    class Config:
        orm_mode = True