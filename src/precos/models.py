from sqlalchemy import Column, Integer, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from src.database import Base

class Preco(Base):
    __tablename__ = "Precos"

    artigo_id = Column(Integer, ForeignKey("Artigos.id"), primary_key=True)
    entidade_id = Column(Integer, ForeignKey("Entidades.id"), primary_key=True)
    valor_entidade = Column(Numeric(10, 2), nullable=False)
    valor_paciente = Column(Numeric(10, 2), nullable=False)
    
    # relacionamentos
    artigo = relationship("ArtigoMedico", back_populates="precos")
    entidade = relationship("Entidade", back_populates="precos")
