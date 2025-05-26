from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

# -------------------- Consulta --------------------

class ConsultaBase(BaseModel):
    paciente_id:    int          = Field(..., description="ID do paciente")
    clinica_id:     int          = Field(..., description="ID da clínica")
    medico_id:      Optional[int] = Field(None, description="ID do médico (opcional até atribuir)")
    entidade_id:    int          = Field(..., description="ID da entidade (seguro ou particular)")
    sala:           Optional[str] = Field(None, description="Sala da consulta")
    observacoes:    Optional[str] = Field(None, description="Observações livres")

class ConsultaCreate(ConsultaBase):
    pass

class ConsultaRead(ConsultaBase):
    id:           int
    data_inicio:  datetime       = Field(..., description="Timestamp de início da consulta")
    data_fim:     Optional[datetime] = Field(None, description="Timestamp de fim da consulta")
    estado:       str            = Field(..., description="Estado da consulta")
    created_at:   datetime       = Field(..., description="Timestamp de criação")
    updated_at:   datetime       = Field(..., description="Timestamp da última atualização")

    class Config:
        orm_mode = True

# ----------------- ConsultaItem -----------------

class ConsultaItemBase(BaseModel):
    artigo_id:      int          = Field(..., description="ID do artigo/procedimento")
    quantidade:     Optional[int] = Field(1, description="Número de unidades")
    preco_unitario: float        = Field(..., description="Preço unitário do artigo")
    numero_dente:   Optional[int] = Field(None, description="Número do dente (1–32)")
    face:           Optional[List[str]] = Field(
        None,
        description="Faces do dente (ex.: ['M','D','V','L','O','I'])"
    )

class ConsultaItemCreate(ConsultaItemBase):
    pass

class ConsultaItemRead(ConsultaItemBase):
    id:    int    = Field(..., description="ID do item da consulta")
    total: float  = Field(..., description="Total calculado (quantidade × preço_unitário)")

    class Config:
        orm_mode = True

# ------------- Leitura completa da Consulta -------------

class ConsultaFull(ConsultaRead):
    itens: List[ConsultaItemRead] = Field(
        ..., description="Lista de itens (artigos/procedimentos) associados"
    )

# ------------------ Atualização de Consulta ------------------
class ConsultaUpdate(BaseModel):
    paciente_id:   Optional[int]      = None
    clinica_id:    Optional[int]      = None
    medico_id:     Optional[int]      = None
    entidade_id:   Optional[int]      = None
    sala:          Optional[str]      = None
    observacoes:   Optional[str]      = None
    data_inicio:   Optional[datetime] = None
    data_fim:      Optional[datetime] = None
    estado:        Optional[str]      = None

    class Config:
        orm_mode = True


# ------------- Atualização de Item da Consulta --------------
class ConsultaItemUpdate(BaseModel):
    artigo_id:      Optional[int]      = None
    quantidade:     Optional[int]      = None
    preco_unitario: Optional[float]    = None
    numero_dente:   Optional[int]      = None
    face:           Optional[List[str]] = None

    class Config:
        orm_mode = True