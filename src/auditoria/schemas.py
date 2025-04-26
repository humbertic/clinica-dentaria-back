from pydantic import BaseModel
from datetime import datetime

class AuditoriaResponse(BaseModel):
    id: int
    utilizador_id: int
    utilizador_nome: str | None = None
    acao: str
    objeto: str
    objeto_id: int | None = None
    objeto_nome: str | None = None
    detalhes: str | None = None
    data: datetime

    class Config:
        from_attributes = True