from sqlalchemy import Column, Integer, String, SmallInteger
from src.database import Base
from sqlalchemy.orm import relationship


class Dente(Base):
    __tablename__ = "Dentes"

    id         = Column(SmallInteger, primary_key=True)   # 11-48, 51-85
    codigo_fdi = Column(String(2), unique=True, nullable=False)
    tipo       = Column(String(10), nullable=False)       # permanente | deciduo
    arcada     = Column(String(10), nullable=False)       # superior  | inferior
    quadrante  = Column(SmallInteger, nullable=False)     # 1-8
    posicao    = Column(SmallInteger, nullable=False)     # 1-8 ou 1-5
    classe     = Column(String(20), nullable=False)

class Face(Base):
    __tablename__ = "Faces"

    id        = Column(String(1), primary_key=True)       # M,D,V,L,O,I
    descricao = Column(String(20), nullable=False)
