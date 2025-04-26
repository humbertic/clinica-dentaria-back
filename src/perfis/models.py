from sqlalchemy import Column, Integer, String
from src.database import Base

class Perfil(Base):
    __tablename__ = "Perfil"

    id = Column(Integer, primary_key=True)
    perfil = Column(String(50), nullable=False, unique=True)
    nome = Column(String(50), nullable=False, unique=True)