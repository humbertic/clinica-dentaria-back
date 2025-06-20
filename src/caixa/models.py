import enum
from sqlalchemy import (
    Column, Integer, Numeric, DateTime, ForeignKey, String, Text, Enum as SAEnum, func
)
from sqlalchemy.orm import relationship
from src.database import Base
from src.comuns.enums import MetodoPagamento

class CaixaStatus(enum.Enum):
    aberto = "aberto"
    fechado = "fechado"

class CaixaSession(Base):
    __tablename__ = "CaixaSessions"

    id            = Column(Integer, primary_key=True, index=True)
    operador_id   = Column(Integer, ForeignKey("Utilizador.id"), nullable=False)
    data_inicio   = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    valor_inicial = Column(Numeric(12,2), nullable=False)
    status        = Column(SAEnum(CaixaStatus), nullable=False, default=CaixaStatus.aberto)
    valor_final   = Column(Numeric(12,2), nullable=True)
    data_fecho    = Column(DateTime(timezone=True), nullable=True)

    operador      = relationship("Utilizador")
    payments      = relationship("CashierPayment", back_populates="session", cascade="all, delete-orphan")

class CashierPayment(Base):
    __tablename__ = "CaixaPayments"

    id               = Column(Integer, primary_key=True, index=True)
    session_id       = Column(Integer, ForeignKey("CaixaSessions.id"), nullable=False)
    fatura_id        = Column(Integer, ForeignKey("Faturas.id"), nullable=True)
    parcela_id       = Column(Integer, ForeignKey("ParcelasPagamento.id"), nullable=True)
    valor_pago       = Column(Numeric(12,2), nullable=False)
    metodo_pagamento = Column(SAEnum(MetodoPagamento), nullable=True)
    data_pagamento   = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    observacoes      = Column(Text, nullable=True)
    operador_id      = Column(Integer, ForeignKey("Utilizador.id"), nullable=False)

    session          = relationship("CaixaSession", back_populates="payments")
    operador         = relationship("Utilizador")
