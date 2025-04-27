from sqlalchemy import Column, Integer, String, Text, Boolean, Date, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.orm import relationship
from src.database import Base

class ItemStock(Base):
    __tablename__ = "ItemStock"
    id = Column(Integer, primary_key=True)
    clinica_id = Column(Integer, ForeignKey("Clinica.id"))
    nome = Column(String(100), nullable=False)
    descricao = Column(Text)
    lote = Column(String(50))
    quantidade_atual = Column(Integer, nullable=False)
    quantidade_minima = Column(Integer, nullable=False)
    validade = Column(Date)
    tipo_medida = Column(String(30), nullable=False)
    fornecedor = Column(String(100))
    ativo = Column(Boolean, default=True)

class MovimentoStock(Base):
    __tablename__ = "MovimentoStock"
    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey("ItemStock.id"))
    tipo_movimento = Column(String(50), nullable=False)
    quantidade = Column(Integer, nullable=False)
    data = Column(Date)
    utilizador_id = Column(Integer, ForeignKey("Utilizador.id"))
    justificacao = Column(Text)

class ItemFilial(Base):
    __tablename__ = "ItemFilial"
    item_id = Column(Integer, ForeignKey("ItemStock.id"), primary_key=True)
    filial_id = Column(Integer, ForeignKey("Clinica.id"), primary_key=True)
    quantidade = Column(Integer, nullable=False)