from sqlalchemy import Column, Integer, SmallInteger, String, ForeignKey, UniqueConstraint, Boolean
from sqlalchemy.orm import relationship
from src.database import Base

from src.categoria.models import Categoria

class ArtigoMedico(Base):
    __tablename__ = "Artigos"
    __table_args__ = (
        UniqueConstraint("codigo", "descricao", "categoria_id", name="uix_codigo_descricao_categoria"),
    )

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, nullable=False, index=True)
    descricao = Column(String, nullable=False)
    categoria_id = Column(Integer, ForeignKey("Categorias.id"), nullable=False)
    requer_dente = Column(Boolean, nullable=False, default=False)
    requer_face  = Column(Boolean, nullable=False, default=False) 
    face_count   = Column(SmallInteger, nullable=True)
    
    precos = relationship(
        "Preco",               
        back_populates="artigo",
        cascade="all, delete-orphan"
    )
    
    categoria = relationship(
        Categoria,
        back_populates="artigos"
    )