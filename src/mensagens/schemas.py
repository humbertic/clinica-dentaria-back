from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class MessageBase(BaseModel):
    texto: str
    clinica_id: int          


class MessageCreate(BaseModel):
    clinica_id: int
    thread_id: Optional[int] = None
    destinatario_id: Optional[int] = None
    texto: str
    tipo_thread: Optional[str] = "dm"  # "dm", "clinic", "group"

class MessageRead(MessageBase):
    id: int
    thread_id: int | None = None
    remetente_id: int
    remetente_nome: Optional[str] = None
    created_at: datetime
    lida: bool

    class Config:
        orm_mode = True


class ThreadRead(BaseModel):
    id: int
    clinica_id: int
    tipo: str  # "dm", "clinic", "group"
    nome: Optional[str] = None
    outro_participante_id: Optional[int] = None  
    outro_participante_nome: Optional[str] = None
    
    class Config:
        from_attributes = True
