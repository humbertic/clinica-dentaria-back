from sqlalchemy import Column, Integer, String
from src.database import Base
from sqlalchemy.orm import relationship

class Categoria(Base):
    __tablename__ = "Categorias"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String, unique=True, nullable=False, index=True)
    nome = Column(String, nullable=False)
    ordem = Column(Integer, default=0, nullable=False)
    
    artigos = relationship(
        "ArtigoMedico",                         # nome da classe alvo
        back_populates="categoria",             # must match o atributo em ArtigoMedico
        cascade="all, delete-orphan"            # elimina artigos órfãos
    )
