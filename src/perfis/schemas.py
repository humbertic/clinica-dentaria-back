from pydantic import BaseModel

class PerfilBase(BaseModel):
    nome: str

class PerfilCreate(PerfilBase):
    pass

class PerfilUpdate(PerfilBase):
    pass


class PerfilResponse(PerfilBase):
    id: int
    perfil: str

    class Config:
        from_attributes = True