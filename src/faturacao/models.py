from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from datetime import datetime
import enum
from sqlalchemy import (
    Column, Integer, Numeric, DateTime, ForeignKey, String, Enum as SAEnum, func, CheckConstraint
)
from sqlalchemy.orm import relationship
from src.database import Base
from src.comuns.enums import MetodoPagamento

metodopagamento_enum = PG_ENUM(
    *[m.value for m in MetodoPagamento], 
    name='metodopagamento',
    create_type=True,
    schema=None  # Use your schema name if you have one
)

class FaturaTipo(enum.Enum):
    consulta = "consulta"
    plano    = "plano"


class FaturaEstado(enum.Enum):
    pendente  = "pendente"
    parcial   = "parcial"
    paga      = "paga"
    cancelada = "cancelada"


class ParcelaEstado(enum.Enum):
    pendente = "pendente"
    parcial  = "parcial"
    paga     = "paga"



class Fatura(Base):
    __tablename__ = "Faturas"

    id           = Column(Integer, primary_key=True, index=True)
    paciente_id  = Column(Integer, ForeignKey("Paciente.id"), nullable=False)
    data_emissao = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    tipo         = Column(SAEnum(FaturaTipo), nullable=False)
    consulta_id  = Column(Integer, ForeignKey("Consultas.id"), nullable=True)
    plano_id     = Column(Integer, ForeignKey("PlanoTratamento.id"), nullable=True)

    total        = Column(Numeric(12,2), nullable=False)
    estado       = Column(SAEnum(FaturaEstado), nullable=False, default=FaturaEstado.pendente)

    # relações
    paciente     = relationship("Paciente", back_populates="faturas")
    consulta     = relationship("Consulta", back_populates="faturas")
    plano        = relationship("PlanoTratamento", back_populates="faturas")
    itens        = relationship("FaturaItem", back_populates="fatura", cascade="all, delete-orphan")
    parcelas     = relationship("ParcelaPagamento", back_populates="fatura", cascade="all, delete-orphan")
    pagamentos = relationship("FaturaPagamento", back_populates="fatura", cascade="all, delete-orphan")

class FaturaItem(Base):
    __tablename__ = "FaturaItens"

    id             = Column(Integer, primary_key=True, index=True)
    fatura_id      = Column(Integer, ForeignKey("Faturas.id"), nullable=False)

    # identifica se vem de consulta_item ou de plano_item
    origem_tipo    = Column(String(20), nullable=False)  
    origem_id      = Column(Integer, nullable=False)

    quantidade     = Column(Integer, nullable=False, default=1)
    preco_unitario = Column(Numeric(10,2), nullable=False)
    total          = Column(Numeric(12,2), nullable=False)
    descricao      = Column(String(255), nullable=False)

    fatura         = relationship("Fatura", back_populates="itens")


class ParcelaPagamento(Base):
    __tablename__ = "ParcelasPagamento"

    id              = Column(Integer, primary_key=True, index=True)
    fatura_id       = Column(Integer, ForeignKey("Faturas.id"), nullable=False)
    numero          = Column(Integer, nullable=False)
    valor_planejado = Column(Numeric(12,2), nullable=False)
    data_vencimento = Column(DateTime(timezone=True), nullable=True)

    valor_pago      = Column(Numeric(12,2), nullable=True)
    data_pagamento  = Column(DateTime(timezone=True), nullable=True)
    estado          = Column(SAEnum(ParcelaEstado), nullable=False, default=ParcelaEstado.pendente)

    metodo_pagamento = Column(metodopagamento_enum, nullable=True)

    fatura          = relationship("Fatura", back_populates="parcelas")


class FaturaPagamento(Base):
    __tablename__ = "fatura_pagamentos"
    
    id = Column(Integer, primary_key=True, index=True)
    fatura_id = Column(Integer, ForeignKey("Faturas.id", ondelete="CASCADE"), nullable=False)
    valor = Column(Numeric(10, 2), nullable=False)
    data_pagamento = Column(DateTime, nullable=False, default=datetime.utcnow)
    metodo_pagamento = Column(metodopagamento_enum, nullable=True)
    observacoes = Column(String, nullable=True)
    
    # Relationship
    fatura = relationship("Fatura", back_populates="pagamentos")