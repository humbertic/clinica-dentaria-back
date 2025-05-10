from datetime import date, datetime
from typing import List, Optional, Dict, Any


from pydantic import BaseModel, EmailStr, constr, Field
from src.clinica.schemas import ClinicaMinimalResponse


# -------------------------------------------------
# ---------- PACIENTE -----------------------------
# -------------------------------------------------
class PacienteCreate(BaseModel):
    clinica_id: int
    nome: constr(min_length=1, max_length=100)
    nif: Optional[constr(min_length=4, max_length=20)] = None
    data_nascimento: Optional[date] = None
    sexo: Optional[constr(min_length=1, max_length=10)] = None
    telefone: Optional[constr(min_length=7, max_length=20)] = None
    email: Optional[EmailStr] = None
    nacionalidade: Optional[str] = None
    tipo_documento: Optional[str] = None
    numero_documento: Optional[str] = None
    validade_documento: Optional[date] = None
    pais_residencia: Optional[str] = None
    morada: Optional[str] = None


class PacienteUpdate(BaseModel):
    nome: Optional[constr(min_length=1, max_length=100)] = None
    nif: Optional[constr(min_length=4, max_length=20)] = None
    data_nascimento: Optional[date] = None
    sexo: Optional[constr(min_length=1, max_length=10)] = None
    telefone: Optional[constr(min_length=7, max_length=20)] = None
    email: Optional[EmailStr] = None
    nacionalidade: Optional[str] = None
    tipo_documento: Optional[str] = None
    numero_documento: Optional[str] = None
    validade_documento: Optional[date] = None
    pais_residencia: Optional[str] = None
    morada: Optional[str] = None

class PacienteMinimalResponse(BaseModel):
    id: int
    nome: str

    class Config:
        orm_mode = True


# -------------------------------------------------
# ---------- FICHA CLÍNICA ------------------------
# -------------------------------------------------

class FichaClinicaBase(BaseModel):
    estado_civil: Optional[str] = None
    profissao: Optional[str] = None
    endereco: Optional[str] = None
    telefone: Optional[str] = None
    local_trabalho: Optional[str] = None
    telefone_trabalho: Optional[str] = None
    tipo_beneficiario: Optional[str] = None
    numero_beneficiario: Optional[str] = None
    recomendado_por: Optional[str] = None
    data_questionario: Optional[date] = None

    queixa_principal: Optional[str] = None

    # armazena respostas "Sim/Não" e detalhes do questionário médico
    historia_medica: Optional[Dict[str, Any]] = None

    exame_clinico: Optional[str] = None

    # mapa dentário e anotações por dente
    plano_geral: Optional[Dict[str, Any]] = None

    observacoes_finais: Optional[str] = None
    
    
class FichaClinicaCreate(FichaClinicaBase):
    paciente_id: int = Field(..., description="ID do paciente associado à ficha clínica")

class FichaClinicaUpdate(FichaClinicaBase):
    pass


class FichaClinicaResponse(FichaClinicaBase):
    id: int
    paciente_id: int
    data_criacao: datetime
    responsavel_criacao_id: int
    responsavel_atualizacao_id: Optional[int] = None
    data_atualizacao: Optional[datetime] = None

    class Config:
        orm_mode = True


# -------------------------------------------------
# ---------- ANOTAÇÃO CLÍNICA ---------------------
# -------------------------------------------------
class AnotacaoClinicaCreate(BaseModel):
    ficha_id: int
    texto: constr(min_length=1)


class AnotacaoClinicaResponse(BaseModel):
    id: int
    ficha_id: int
    texto: str
    data: datetime

    class Config:
        orm_mode = True


# -------------------------------------------------
# ---------- FICHEIRO CLÍNICO ---------------------
# -------------------------------------------------
class FicheiroClinicoCreate(BaseModel):
    ficha_id: int
    tipo: str                # ex.: "radiografia"
    caminho_ficheiro: str


class FicheiroClinicoResponse(BaseModel):
    id: int
    ficha_id: int
    tipo: str
    caminho_ficheiro: str
    data_upload: datetime

    class Config:
        orm_mode = True


# -------------------------------------------------
# ---------- PLANO DE TRATAMENTO ------------------
# -------------------------------------------------
class PlanoTratamentoCreate(BaseModel):
    paciente_id: int
    descricao: str


class PlanoTratamentoUpdate(BaseModel):
    descricao: Optional[str] = None
    estado: Optional[str] = None   # em_curso / concluido_parcial / concluido_total


class PlanoTratamentoResponse(BaseModel):
    id: int
    paciente_id: int
    descricao: str
    estado: Optional[str] = None

    class Config:
        orm_mode = True


# -------------------------------------------------
# ---------- RESPOSTAS COMPLETAS ------------------
# -------------------------------------------------
class FichaClinicaWithChildren(FichaClinicaResponse):
    anotacoes: List[AnotacaoClinicaResponse] = []
    ficheiros: List[FicheiroClinicoResponse] = []


class PacienteResponse(BaseModel):
    id: int
    nome: str
    nif: Optional[str] = None
    data_nascimento: Optional[date] = None
    sexo: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[EmailStr] = None
    nacionalidade: Optional[str] = None
    tipo_documento: Optional[str] = None
    numero_documento: Optional[str] = None
    validade_documento: Optional[date] = None
    pais_residencia: Optional[str] = None
    morada: Optional[str] = None
    clinica: ClinicaMinimalResponse
    fichas: List[FichaClinicaWithChildren] = []
    planos: List[PlanoTratamentoResponse] = []

    class Config:
        orm_mode = True

class PacienteListItemResponse(BaseModel):
    id: int
    nome: str
    nif: str | None = None
    data_nascimento: date | None = None
    sexo: str | None = None
    telefone: str | None = None
    email: EmailStr | None = None
    nacionalidade: Optional[str] = None
    tipo_documento: Optional[str] = None
    numero_documento: Optional[str] = None
    validade_documento: Optional[date] = None
    pais_residencia: Optional[str] = None
    morada: Optional[str] = None
    clinica: ClinicaMinimalResponse

    class Config:
        orm_mode = True