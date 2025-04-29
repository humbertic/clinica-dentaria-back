from sqlalchemy import Column, Integer, String, Text, Boolean, Date, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from src.database import Base
from datetime import datetime

class ItemStock(Base):
    __tablename__ = "ItemStock"
    id = Column(Integer, primary_key=True)
    clinica_id = Column(Integer, ForeignKey("Clinica.id"))
    nome = Column(String(100), nullable=False)
    descricao = Column(Text)
    # quantidade_atual = Column(Integer, nullable=False)
    quantidade_minima = Column(Integer, nullable=False)
    tipo_medida = Column(String(30), nullable=False)
    fornecedor = Column(String(100))
    ativo = Column(Boolean, default=True)

    # Relationships
    movimentos = relationship("MovimentoStock", back_populates="item")
    filiais = relationship("ItemFilial", back_populates="item")
    lotes = relationship("ItemLote", back_populates="item")  
    
class MovimentoStock(Base):
    __tablename__ = "MovimentoStock"
    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey("ItemStock.id"))
    tipo_movimento = Column(String(50), nullable=False)
    quantidade = Column(Integer, nullable=False)
    data = Column(DateTime, default=datetime.utcnow)
    utilizador_id = Column(Integer, ForeignKey("Utilizador.id"))
    justificacao = Column(Text)

    # Relationships
    utilizador = relationship("Utilizador")
    item = relationship("ItemStock", back_populates="movimentos")

class ItemFilial(Base):
    __tablename__ = "ItemFilial"
    item_id = Column(Integer, ForeignKey("ItemStock.id"), primary_key=True)
    filial_id = Column(Integer, ForeignKey("Clinica.id"), primary_key=True)
    quantidade = Column(Integer, nullable=False)

    # Relationships
    item = relationship("ItemStock", back_populates="filiais")
    # Optionally, if you want to access the clinic object:
    # filial = relationship("Clinica")
    
class ItemLote(Base):
    __tablename__ = "ItemLote"
    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey("ItemStock.id"), nullable=False)
    lote = Column(String(50), nullable=False)
    validade = Column(Date, nullable=False)
    quantidade = Column(Integer, nullable=False)
    # Relacionamento com o item
    item = relationship("ItemStock", back_populates="lotes")