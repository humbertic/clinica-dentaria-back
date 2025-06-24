from pydantic import BaseModel, EmailStr, constr
from typing import Optional
from src.clinica.schemas import ClinicaMinimalResponse
from src.perfis.schemas import PerfilResponse


# ---------- ENTRADA ----------

class UtilizadorCreate(BaseModel):
    username: constr(min_length=3, max_length=50)
    nome: constr(min_length=1, max_length=100)
    email: EmailStr
    telefone: constr(min_length=7, max_length=20)
    password: constr(min_length=6)
    
    
class UtilizadorAdminUpdate(BaseModel):
    nome: constr(min_length=1, max_length=100)
    telefone: constr(min_length=7, max_length=20)
    ativo: Optional[bool] = None  # For activate/deactivate

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    
    
    
class UtilizadorUpdate(BaseModel):
    nome: constr(min_length=1, max_length=100)
    telefone: constr(min_length=7, max_length=20)
    
    

class AtribuirPerfilRequest(BaseModel):
    perfil_id: int

class AtribuirClinicaRequest(BaseModel):
    clinica_ids: list[int]
    
    
class UtilizadorClinicaResponse(BaseModel):
    clinica: ClinicaMinimalResponse | None = None
    # perfil: PerfilResponse | None = None

    class Config:
        orm_mode = True


# ---------- SAÍDA ----------

class UtilizadorResponse(BaseModel):
    id: int
    username: str
    nome: str
    email: str
    telefone: str | None = None
    ativo: bool
    bloqueado: bool
    perfil: PerfilResponse | None = None 
    clinicas: list[UtilizadorClinicaResponse] = []
    

    class Config:
        orm_mode = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: Optional[int] = None
    
    
class AlterarSenhaRequest(BaseModel):
    senha_atual: str
    nova_senha: str
