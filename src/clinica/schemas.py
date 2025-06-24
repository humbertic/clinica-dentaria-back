from typing import Optional
from pydantic import BaseModel

# -------- CLINICA --------
class ClinicaBase(BaseModel):
    nome: str
    email_envio: str | None = None
    morada: str | None = None
    clinica_pai_id: int | None = None
    partilha_dados: bool = False

class ClinicaParentInfo(BaseModel):
    id:   int
    nome: str

    class Config:
        orm_mode = True

class ClinicaCreate(ClinicaBase):
    pass

class ClinicaResponse(ClinicaBase):
    id: int
    criado_por_id: int | None = None
    clinica_pai:  Optional[ClinicaParentInfo]

    class Config:
        from_attributes = True
        
        
class ClinicaMinimalResponse(BaseModel):
    id: int
    nome: str

    class Config:
        orm_mode = True  

# -------- CLINICA CONFIGURACAO --------
class ClinicaConfiguracaoBase(BaseModel):
    chave: str
    valor: str

class ClinicaConfiguracaoCreate(ClinicaConfiguracaoBase):
    clinica_id: int | None = None
    
class ClinicaConfiguracaoResponse(ClinicaConfiguracaoBase):
    id: int
    clinica_id: int | None = None

    class Config:
        from_attributes = True

# -------- CLINICA EMAIL --------
class ClinicaEmailBase(BaseModel):
    remetente: str | None = None
    smtp_host: str | None = None
    smtp_porta: int | None = None
    utilizador_smtp: str | None = None
    password_smtp: str | None = None
    ativo: bool = True

class ClinicaEmailCreate(ClinicaEmailBase):
    clinica_id: int

class ClinicaEmailResponse(ClinicaEmailBase):
    id: int
    clinica_id: int

    class Config:
        from_attributes = True