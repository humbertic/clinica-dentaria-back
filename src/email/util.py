from sqlalchemy.orm import Session
from fastapi import HTTPException, Depends
from typing import Optional

from src.database import SessionLocal
from src.clinica.models import ClinicaEmail
from src.email.schemas import EmailConfig

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_email_config(clinica_id: int, db: Session = Depends(get_db)) -> EmailConfig:
    """
    Get email configuration for a clinic.
    
    Args:
        clinica_id: The ID of the clinic
        db: Database session
        
    Returns:
        EmailConfig: The email configuration
        
    Raises:
        HTTPException: If no active email configuration is found
    """
    # Get the active email configuration for the clinic
    email_config = db.query(ClinicaEmail).filter(
        ClinicaEmail.clinica_id == clinica_id,
        ClinicaEmail.ativo == True
    ).first()
    
    if not email_config:
        raise HTTPException(
            status_code=404,
            detail="Configuração de email não encontrada ou inativa para esta clínica"
        )
    # Convert to Pydantic model
    return EmailConfig.model_validate(email_config)

async def test_email_config(config: EmailConfig) -> bool:
    """
    Test if the email configuration is valid.
    
    Args:
        config: The email configuration to test
        
    Returns:
        bool: True if the configuration is valid
        
    Raises:
        HTTPException: If the configuration is invalid
    """
    from .service import EmailService
    
    try:
        # Create email service
        email_service = EmailService(config)
        
        # If no error is raised, the configuration is valid
        return True
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Configuração de email inválida: {str(e)}"
        )