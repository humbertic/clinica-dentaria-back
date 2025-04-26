from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database import SessionLocal
from src.utilizadores.dependencies import get_current_user
from src.utilizadores.utils import is_master_admin
from . import service, schemas, models
from src.utilizadores import models as utilizador_models

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------- CLINICA --------
@router.post("", response_model=schemas.ClinicaResponse)
def criar_clinica(
    dados: schemas.ClinicaCreate,
    db: Session = Depends(get_db),
    utilizador_atual: utilizador_models.Utilizador = Depends(get_current_user)
):
    if not is_master_admin(utilizador_atual):
        raise HTTPException(status_code=403, detail="Apenas o Master Admin pode criar clínica.")
    return service.criar_clinica(db, dados, criado_por_id=utilizador_atual.id)

@router.put("/{clinica_id}", response_model=schemas.ClinicaResponse)
def atualizar_clinica(
    clinica_id: int,
    dados: schemas.ClinicaCreate,
    db: Session = Depends(get_db),
    utilizador_atual: utilizador_models.Utilizador = Depends(get_current_user)
):
    if not is_master_admin(utilizador_atual):
        raise HTTPException(status_code=403, detail="Apenas o Master Admin pode atualizar clínica.")
    clinica = service.atualizar_clinica(db, clinica_id, dados, utilizador_atual.id)
    if not clinica:
        raise HTTPException(status_code=404, detail="Clínica não encontrada.")
    return clinica

# -------- CLINICA CONFIGURACAO --------
@router.post("/configuracoes", response_model=schemas.ClinicaConfiguracaoResponse)
def criar_configuracao(
    dados: schemas.ClinicaConfiguracaoCreate,
    db: Session = Depends(get_db),
    utilizador_atual: utilizador_models.Utilizador = Depends(get_current_user)
):
    if not is_master_admin(utilizador_atual):
        raise HTTPException(status_code=403, detail="Apenas o Master Admin pode criar configuração.")
    return service.criar_configuracao(db, dados, utilizador_atual.id)

@router.put("/configuracoes/{config_id}", response_model=schemas.ClinicaConfiguracaoResponse)
def atualizar_configuracao(
    config_id: int,
    dados: schemas.ClinicaConfiguracaoBase,
    db: Session = Depends(get_db),
    utilizador_atual: utilizador_models.Utilizador = Depends(get_current_user)
):
    if not is_master_admin(utilizador_atual):
        raise HTTPException(status_code=403, detail="Apenas o Master Admin pode atualizar configuração.")
    config = service.atualizar_configuracao(db, config_id, dados, utilizador_atual.id)
    if not config:
        raise HTTPException(status_code=404, detail="Configuração não encontrada.")
    return config

@router.delete("/configuracoes/{config_id}", response_model=dict)
def remover_configuracao(
    config_id: int,
    db: Session = Depends(get_db),
    utilizador_atual: utilizador_models.Utilizador = Depends(get_current_user)
):
    if not is_master_admin(utilizador_atual):
        raise HTTPException(status_code=403, detail="Apenas o Master Admin pode remover configuração.")
    config = service.remover_configuracao(db, config_id, utilizador_atual.id)
    if not config:
        raise HTTPException(status_code=404, detail="Configuração não encontrada.")
    return {"detail": "Configuração removida com sucesso."}

# -------- CLINICA EMAIL --------
@router.post("/emails", response_model=schemas.ClinicaEmailResponse)
def criar_email(
    dados: schemas.ClinicaEmailCreate,
    db: Session = Depends(get_db),
    utilizador_atual: utilizador_models.Utilizador = Depends(get_current_user)
):
    if not is_master_admin(utilizador_atual):
        raise HTTPException(status_code=403, detail="Apenas o Master Admin pode criar e-mail SMTP.")
    return service.criar_email(db, dados, utilizador_atual.id)

@router.put("/emails/{email_id}", response_model=schemas.ClinicaEmailResponse)
def atualizar_email(
    email_id: int,
    dados: schemas.ClinicaEmailBase,
    db: Session = Depends(get_db),
    utilizador_atual: utilizador_models.Utilizador = Depends(get_current_user)
):
    if not is_master_admin(utilizador_atual):
        raise HTTPException(status_code=403, detail="Apenas o Master Admin pode atualizar e-mail SMTP.")
    email = service.atualizar_email(db, email_id, dados, utilizador_atual.id)
    if not email:
        raise HTTPException(status_code=404, detail="E-mail SMTP não encontrado.")
    return email

@router.delete("/emails/{email_id}", response_model=dict)
def remover_email(
    email_id: int,
    db: Session = Depends(get_db),
    utilizador_atual: utilizador_models.Utilizador = Depends(get_current_user)
):
    if not is_master_admin(utilizador_atual):
        raise HTTPException(status_code=403, detail="Apenas o Master Admin pode remover e-mail SMTP.")
    email = service.remover_email(db, email_id, utilizador_atual.id)
    if not email:
        raise HTTPException(status_code=404, detail="E-mail SMTP não encontrado.")
    return {"detail": "E-mail SMTP removido com sucesso."}


@router.get("", response_model=list[schemas.ClinicaResponse])
def listar_clinicas(
    db: Session = Depends(get_db),
    utilizador_atual: utilizador_models.Utilizador = Depends(get_current_user)
):
    return service.listar_clinicas(db, utilizador_atual)

@router.get("/{clinica_id}", response_model=schemas.ClinicaResponse)
def obter_clinica_por_id(
    clinica_id: int,
    db: Session = Depends(get_db),
    utilizador_atual: utilizador_models.Utilizador = Depends(get_current_user)
):
    if not is_master_admin(utilizador_atual):
        raise HTTPException(status_code=403, detail="Apenas o Master Admin pode visualizar clínica.")
    clinica = service.obter_clinica_por_id(db, clinica_id, utilizador_atual)
    if not clinica:
        raise HTTPException(status_code=404, detail="Clínica não encontrada.")
    return clinica

@router.get("/configuracoes/{clinica_id}", response_model=list[schemas.ClinicaConfiguracaoResponse])
def listar_configuracoes(
    clinica_id: int,
    db: Session = Depends(get_db),
    utilizador_atual: utilizador_models.Utilizador = Depends(get_current_user)
):
    if not is_master_admin(utilizador_atual):
        raise HTTPException(status_code=403, detail="Apenas o Master Admin pode listar configurações.")
    return service.listar_configuracoes(db, clinica_id)

@router.get("/emails/{clinica_id}", response_model=list[schemas.ClinicaEmailResponse])
def listar_emails(
    clinica_id: int,
    db: Session = Depends(get_db),
    utilizador_atual: utilizador_models.Utilizador = Depends(get_current_user)
):
    if not is_master_admin(utilizador_atual):
        raise HTTPException(status_code=403, detail="Apenas o Master Admin pode listar e-mails SMTP.")
    return service.listar_emails(db, clinica_id)