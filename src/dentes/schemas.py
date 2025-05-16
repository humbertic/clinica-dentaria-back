from pydantic import BaseModel


class FaceResponse(BaseModel):
    id: str
    descricao: str

    class Config:
        orm_mode = True


class DenteResponse(BaseModel):
    id: int
    codigo_fdi: str
    tipo: str
    arcada: str
    quadrante: int
    posicao: int
    classe: str

    class Config:
        orm_mode = True