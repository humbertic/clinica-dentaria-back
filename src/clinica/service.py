from src.utilizadores.models import Utilizador, UtilizadorClinica
from src.utilizadores.utils import is_master_admin
from src.auditoria.utils import registrar_auditoria
from sqlalchemy.orm import Session, selectinload
from src.clinica import models, schemas

def criar_clinica(db: Session, dados: schemas.ClinicaCreate, criado_por_id: int):
    clinica = models.Clinica(**dados.dict(), criado_por_id=criado_por_id)
    db.add(clinica)
    db.commit()
    db.refresh(clinica)
    # Copy global configurations to new clinic
    global_configs = db.query(models.ClinicaConfiguracao).filter_by(clinica_id=None).all()
    for config in global_configs:
        new_config = models.ClinicaConfiguracao(
            clinica_id=clinica.id,
            chave=config.chave,
            valor=config.valor,
        )
        db.add(new_config)
    db.commit()
    registrar_auditoria(
        db, criado_por_id, "Criação", "Clinica", clinica.id, f"Clínica '{clinica.nome}' criada."
    )
    return clinica

def atualizar_clinica(db: Session, clinica_id: int, dados: schemas.ClinicaCreate, user_id: int):
    clinica = db.query(models.Clinica).filter_by(id=clinica_id).first()
    if not clinica:
        return None
    for key, value in dados.dict().items():
        setattr(clinica, key, value)
    db.commit()
    db.refresh(clinica)
    registrar_auditoria(
        db, user_id, "Atualização", "Clinica", clinica.id, f"Clínica '{clinica.nome}' atualizada."
    )
    return clinica

def criar_configuracao(db: Session, dados: schemas.ClinicaConfiguracaoCreate, user_id: int):
    if dados.clinica_id is None:
        exists = db.query(models.ClinicaConfiguracao).filter_by(
            clinica_id=None, chave=dados.chave
        ).first()
    else:
        exists = db.query(models.ClinicaConfiguracao).filter_by(
            clinica_id=dados.clinica_id, chave=dados.chave
        ).first()
    if exists:
        raise ValueError("Configuração com essa chave já existe.")
    config = models.ClinicaConfiguracao(**dados.dict())
    db.add(config)
    db.commit()
    db.refresh(config)
    if config.clinica_id is None:
        clinics = db.query(models.Clinica).all()
        for clinic in clinics:
            clinic_config = models.ClinicaConfiguracao(
                clinica_id=clinic.id,
                chave=config.chave,
                valor=config.valor,
            )
            db.add(clinic_config)
        db.commit()
    registrar_auditoria(
        db, user_id, "Criação", "ClinicaConfiguracao", config.id, f"Configuração '{config.chave}' criada."
    )
    return config

def atualizar_configuracao(db: Session, config_id: int, dados: schemas.ClinicaConfiguracaoBase, user_id: int):
    config = db.query(models.ClinicaConfiguracao).filter_by(id=config_id).first()
    if not config:
        return None
    for key, value in dados.dict().items():
        setattr(config, key, value)
    db.commit()
    db.refresh(config)
    registrar_auditoria(
        db, user_id, "Atualização", "ClinicaConfiguracao", config.id, f"Configuração '{config.chave}' atualizada."
    )
    return config

def remover_configuracao(db: Session, config_id: int, user_id: int):
    config = db.query(models.ClinicaConfiguracao).filter_by(id=config_id).first()
    if config:
        db.delete(config)
        db.commit()
        registrar_auditoria(
            db, user_id, "Remoção", "ClinicaConfiguracao", config_id, f"Configuração removida."
        )
    return config

def criar_email(db: Session, dados: schemas.ClinicaEmailCreate, user_id: int):
    email = models.ClinicaEmail(**dados.dict())
    db.add(email)
    db.commit()
    db.refresh(email)
    registrar_auditoria(
        db, user_id, "Criação", "ClinicaEmail", email.id, f"E-mail SMTP criado."
    )
    return email

def atualizar_email(db: Session, email_id: int, dados: schemas.ClinicaEmailBase, user_id: int):
    email = db.query(models.ClinicaEmail).filter_by(id=email_id).first()
    if not email:
        return None
    for key, value in dados.dict().items():
        setattr(email, key, value)
    db.commit()
    db.refresh(email)
    registrar_auditoria(
        db, user_id, "Atualização", "ClinicaEmail", email.id, f"E-mail SMTP atualizado."
    )
    return email

def remover_email(db: Session, email_id: int, user_id: int):
    email = db.query(models.ClinicaEmail).filter_by(id=email_id).first()
    if email:
        db.delete(email)
        db.commit()
        registrar_auditoria(
            db, user_id, "Remoção", "ClinicaEmail", email_id, f"E-mail SMTP removido."
        )
    return email

def listar_clinicas(db: Session, utilizador_atual: Utilizador):
    query = db.query(models.Clinica).options(
        selectinload(models.Clinica.clinica_pai)   
    )
    if is_master_admin(utilizador_atual):
        return query.filter(
            models.Clinica.criado_por_id == utilizador_atual.id
        ).all()
    else:
        return (
            query.join(UtilizadorClinica,
                       UtilizadorClinica.clinica_id == models.Clinica.id)
                 .filter(UtilizadorClinica.utilizador_id == utilizador_atual.id)
                 .all()
        )
        
def obter_clinica_por_id(db: Session, clinica_id: int, utilizador_atual):
    return db.query(models.Clinica).filter(models.Clinica.id == clinica_id).first()

def listar_configuracoes(db: Session, clinica_id: int):
    return db.query(models.ClinicaConfiguracao).filter_by(clinica_id=clinica_id).all()

def listar_emails(db: Session, clinica_id: int):
    return db.query(models.ClinicaEmail).filter_by(clinica_id=clinica_id).all()


def get_clinica_details(db: Session):
    """
    Get basic clinic information from the database.
    """
    
    clinica = db.query(models.Clinica).first()
    return clinica