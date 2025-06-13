from datetime import date
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field
from src.entidades.schemas import EntidadeResponse
from src.pacientes.schemas import PacienteMinimalResponse
from src.artigos.schemas import ArtigoMinimal


# -------------------------------
#  Enum para refletir o modelo
# -------------------------------
class EstadoOrc(str, Enum):
    """Usado para o campo estado do orçamento."""
    rascunho  = "rascunho"
    aprovado  = "aprovado"
    rejeitado = "rejeitado"


# -------------------------------
#  SCHEMAS DE ITENS
# -------------------------------

class OrcamentoItemBase(BaseModel):
    artigo_id: int
    quantidade: int = Field(default=1, ge=1)  # Validação de inteiro >= 1

    numero_dente: Optional[int] = None   # 11-48, 51-85
    face: Optional[List[str]] = None   # M,D,V,L,O,I

    preco_entidade: Decimal = Field(..., max_digits=10, decimal_places=2)
    preco_paciente: Decimal = Field(..., max_digits=10, decimal_places=2)
    observacoes: Optional[str] = None
    
    class Config:
        orm_mode = True


class OrcamentoItemCreate(OrcamentoItemBase):
    """Usado pelo endpoint que adiciona um item."""
    pass


class OrcamentoItemRead(OrcamentoItemBase):
    id: int
    subtotal_entidade: Decimal = Field(..., max_digits=12, decimal_places=2)
    subtotal_paciente: Decimal = Field(..., max_digits=12, decimal_places=2)
    artigo: ArtigoMinimal


# -------------------------------
#  SCHEMAS DE ORÇAMENTO
# -------------------------------

class OrcamentoBase(BaseModel):
    paciente_id: int
    entidade_id: int
    data: date = date.today()
    observacoes: Optional[str] = None

    class Config:
        orm_mode = True


class OrcamentoCreate(OrcamentoBase):
    """Cria cabeçalho vazio em estado rascunho."""


class OrcamentoRead(OrcamentoBase):
    id: int
    estado: EstadoOrc
    total_entidade: Decimal
    total_paciente: Decimal
    itens: List[OrcamentoItemRead] = []
    paciente: PacienteMinimalResponse
    entidade: Optional[EntidadeResponse] = None


class OrcamentoUpdateEstado(BaseModel):
    """Body para /orcamentos/{id}/estado"""
    estado: EstadoOrc
    
class OrcamentoUpdate(BaseModel):
    entidade_id: Optional[int] = None
    data: Optional[date] = None
    observacoes: Optional[str] = None
    
    class Config:
        orm_mode = True