from sqlalchemy import Column, Integer, String
from src.database import Base
from sqlalchemy.orm import relationship

class Entidade(Base):
    __tablename__ = "Entidades"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String, unique=True, nullable=False, index=True)
    nome = Column(String, nullable=False)
    
    precos = relationship("Preco", back_populates="entidade", cascade="all, delete-orphan")
