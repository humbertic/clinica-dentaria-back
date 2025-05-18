from sqlalchemy import (
    Column, Integer, Numeric, Date, Enum, ForeignKey, SmallInteger, String, ARRAY, TEXT
)
from sqlalchemy.orm import relationship
from src.database import Base
import enum


class EstadoOrc(str, enum.Enum):  
    rascunho  = "rascunho"
    aprovado  = "aprovado"
    rejeitado = "rejeitado"


class Orcamento(Base):
    __tablename__ = "Orcamentos"

    id              = Column(Integer, primary_key=True)
    paciente_id     = Column(Integer, ForeignKey("Paciente.id"), nullable=False)
    entidade_id     = Column(Integer, ForeignKey("Entidades.id"), nullable=False)
    data            = Column(Date, nullable=False)
    estado          = Column(Enum(EstadoOrc), nullable=False, default=EstadoOrc.rascunho)

    total_entidade  = Column(Numeric(12, 2), default=0, nullable=False)
    total_paciente  = Column(Numeric(12, 2), default=0, nullable=False)

    observacoes     = Column(String, nullable=True)

    itens = relationship("OrcamentoItem", back_populates="orcamento",
                         cascade="all, delete-orphan")
    paciente = relationship("Paciente")
    entidade = relationship("Entidade")


class OrcamentoItem(Base):
    __tablename__ = "OrcamentoItens"

    id                 = Column(Integer, primary_key=True)
    orcamento_id       = Column(Integer, ForeignKey("Orcamentos.id"), nullable=False)
    artigo_id          = Column(Integer, ForeignKey("Artigos.id"), nullable=False)
    quantidade         = Column(Integer, nullable=False, default=1)

    preco_entidade     = Column(Numeric(10, 2), nullable=False)
    preco_paciente     = Column(Numeric(10, 2), nullable=False)
    subtotal_entidade  = Column(Numeric(12, 2), nullable=False)
    subtotal_paciente  = Column(Numeric(12, 2), nullable=False)

    numero_dente       = Column(SmallInteger, nullable=True)
    face = Column(ARRAY(TEXT), nullable=True)       # M,D,V,L,O,I

    orcamento = relationship("Orcamento", back_populates="itens")
    artigo    = relationship("ArtigoMedico")
