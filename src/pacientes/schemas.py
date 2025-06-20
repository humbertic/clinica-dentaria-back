from fastapi import UploadFile, Form, File
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
    caminho_ficheiro: Optional[str] = None


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


class ConsultaMedicoMinimal(BaseModel):
    id: int
    nome: str
    
    class Config:
        orm_mode = True

class ConsultaItemMinimal(BaseModel):
    id: int
    artigo_id: int
    artigo_descricao: Optional[str] = None
    numero_dente: Optional[int] = None
    face: Optional[List[str]] = None
    total: Optional[float] = None
    
    class Config:
        orm_mode = True

class ConsultaEntidadeMinimal(BaseModel):
    id: int
    nome: str
    
    class Config:
        orm_mode = True

class ConsultaMinimalResponse(BaseModel):
    id: int
    data_inicio: datetime
    data_fim: Optional[datetime] = None
    estado: str  # agendada, iniciada, concluida, cancelada, falta
    observacoes: Optional[str] = None
    medico_id: int
    medico: Optional[ConsultaMedicoMinimal] = None
    entidade_id: Optional[int] = None
    entidade: Optional[ConsultaEntidadeMinimal] = None
    itens: List[ConsultaItemMinimal] = []
    
    class Config:
        orm_mode = True

class ArtigoMedicoMinimal(BaseModel):
    id: int
    descricao: str
    codigo: str
    
    class Config:
        orm_mode = True

class PlanoItemResponse(BaseModel):
    id: int
    plano_id: int
    artigo_id: int
    artigo: Optional[ArtigoMedicoMinimal] = None
    quantidade_prevista: int
    quantidade_executada: int
    numero_dente: Optional[int] = None
    face: Optional[List[str]] = None
    estado: str  # pendente, em_curso, concluido, cancelado
    
    class Config:
        orm_mode = True

class PlanoTratamentoDetailResponse(PlanoTratamentoResponse):
    data_criacao: datetime
    data_conclusao: Optional[datetime] = None
    descricao: Optional[str] = None
    itens: List[PlanoItemResponse] = []
    
    class Config:
        from_attributes = True 


class ProcedimentoHistoricoItem(BaseModel):
    id: int
    consulta_id: int
    consulta_data: Optional[str] = None
    artigo_id: int
    artigo_descricao: str
    numero_dente: Optional[int] = None
    face: Optional[List[str]] = None
    total: Optional[float] = None
    medico_id: Optional[int] = None
    medico_nome: Optional[str] = None
    
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
    planos: List[PlanoTratamentoDetailResponse] = []
    consultas: List[ConsultaMinimalResponse] = []
    procedimentos_historico: List[ProcedimentoHistoricoItem] = []


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
    total_consultas: int = 0
    planos_ativos: int = 0
    tem_ficha_clinica: bool = False
    proxima_consulta: Optional[ConsultaMinimalResponse] = None

    class Config:
        orm_mode = True


