from pydantic import BaseModel, EmailStr, validator
from typing import Optional

class EmailConfig(BaseModel):
    """Email configuration model for clinic email settings."""
    smtp_server: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    sender_email: EmailStr
    sender_name: Optional[str] = None
    use_tls: bool = True
    use_ssl: bool = False
    
    @validator('smtp_port')
    def valid_port(cls, v):
        if not (0 < v < 65536):
            raise ValueError('Port must be between 1 and 65535')
        return v
    
    @validator('use_ssl', 'use_tls')
    def not_both_ssl_and_tls(cls, v, values):
        if 'use_tls' in values and values['use_tls'] and v and 'use_ssl' in values.keys():
            raise ValueError('Cannot use both TLS and SSL simultaneously')
        return v

class EmailAttachment(BaseModel):
    """Model for email attachments."""
    content: bytes
    filename: str
    content_type: str = "application/octet-stream"