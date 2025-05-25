from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

# ----------------------------------------------------------------
# Schema base com os campos comuns à criação e leitura
# ----------------------------------------------------------------
class MarcacaoBase(BaseModel):
    paciente_id:   int        = Field(..., description="ID do paciente")
    medico_id:     int        = Field(..., description="ID do médico que irá atender")
    clinic_id:     int        = Field(..., description="ID da clínica")
    agendada_por:  Optional[int] = Field(None, description="ID do utilizador que agendou") 
    entidade_id:   int        = Field(..., description="ID da entidade (particular/seguradora)")
    data_hora_inicio: datetime = Field(..., description="Data e hora de início da marcação")
    data_hora_fim:    datetime = Field(..., description="Data e hora de fim da marcação")
    titulo:          str      = Field(..., description="Título da marcação")
    observacoes:    Optional[str] = Field(None, description="Campo livre de observações")
    estado:         Optional[str] = Field(None, description="Estado da marcação (agendada, falta, iniciada.)")

    class Config:
        orm_mode = True


# ----------------------------------------------------------------
# Schema para criação de marcação
# ----------------------------------------------------------------
class MarcacaoCreate(MarcacaoBase):
    # estado padrão 'rascunho' vem do model, titulo obrigatório
    pass


# ----------------------------------------------------------------
# Schema para atualização parcial
# ----------------------------------------------------------------
class MarcacaoUpdate(BaseModel):
    paciente_id:       Optional[int]     = None
    medico_id:         Optional[int]     = None
    clinic_id:         Optional[int]     = None
    agendada_por:      Optional[int]     = None
    entidade_id:       Optional[int]     = None
    data_hora_inicio:  Optional[datetime] = None
    data_hora_fim:     Optional[datetime] = None
    titulo:            Optional[str]     = None
    observacoes:       Optional[str]     = None
    estado:            Optional[str]     = None

    class Config:
        orm_mode = True
        

class PacienteInfo(BaseModel):
    id: int = Field(..., description="ID do paciente")
    nome: str = Field(..., description="Nome do paciente")
    telefone: str = Field(..., description="Telefone do paciente")

    class Config:
        orm_mode = True


class EntidadeInfo(BaseModel):
    id: int = Field(..., description="ID da entidade")
    slug: str = Field(..., description="Slug da entidade")
    nome: str = Field(..., description="Nome da entidade")

    class Config:
        orm_mode = True


class MarcacaoRead(MarcacaoBase):
    id: int = Field(..., description="ID da marcação")
    created_at: datetime = Field(..., description="Timestamp de criação")
    updated_at: datetime = Field(..., description="Timestamp da última atualização")

    paciente: PacienteInfo   = Field(..., description="Dados básicos do paciente")
    entidade: EntidadeInfo   = Field(..., description="Dados da entidade")

    class Config:
        orm_mode = True


# ----------------------------------------------------------------
# Schema de leitura (response)
# ----------------------------------------------------------------
