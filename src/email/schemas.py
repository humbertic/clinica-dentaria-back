from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional

class EmailAttachment(BaseModel):
    """Model for email attachments."""
    content: bytes
    filename: str
    content_type: str = "application/pdf"

class EmailBase(BaseModel):
    """Base model for email operations."""
    assunto: str
    destinatarios: List[EmailStr]
    corpo: str
    html: bool = False

class EmailComAnexo(EmailBase):
    """Model for email with attachment."""
    anexos: List[EmailAttachment] = []

class EmailConfig(BaseModel):
    """Email configuration from ClinicaEmail model."""
    remetente: EmailStr
    nome_remetente: Optional[str] = None
    smtp_host: str
    smtp_porta: int
    utilizador_smtp: str
    password_smtp: str
    usar_tls: Optional[bool] = True
    usar_ssl: Optional[bool] = False
    ativo: Optional[bool] = True

    class Config:
        from_attributes = True