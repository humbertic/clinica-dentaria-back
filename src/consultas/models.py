from sqlalchemy import (
    ARRAY, Column, Integer, SmallInteger, String, DateTime, ForeignKey, Numeric, Text, func
)
from sqlalchemy.orm import relationship
from src.database import Base
from src.artigos.models import ArtigoMedico

class Consulta(Base):
    __tablename__ = "Consultas"

    id           = Column(Integer, primary_key=True, index=True)
    paciente_id  = Column(Integer, ForeignKey("Paciente.id"), nullable=False)
    clinica_id   = Column(Integer, ForeignKey("Clinica.id"), nullable=False)
    medico_id    = Column(Integer, ForeignKey("Utilizador.id"), nullable=True)
    entidade_id  = Column(Integer, ForeignKey("Entidades.id"), nullable=False)

    data_inicio  = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    data_fim     = Column(DateTime(timezone=True), nullable=True)
    estado       = Column(String(20), nullable=False, default="iniciada")
    observacoes  = Column(String(500), nullable=True)

    created_at   = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at   = Column(DateTime(timezone=True), server_default=func.now(),
                          onupdate=func.now(), nullable=False)

    paciente = relationship(
        "Paciente", 
        back_populates="consultas",
        lazy="joined"
    )
    anotacoes = relationship(
        "AnotacaoClinica", 
        back_populates="consulta",
        cascade="all, delete-orphan"
    )
    
    ficheiros = relationship(
        "FicheiroClinico", 
        back_populates="consulta",
        cascade="all, delete-orphan"
    )
    
    # planos = relationship(
    #     "ConsultaPlanoTratamento", 
    #     back_populates="consulta",
    #     cascade="all, delete-orphan"
    # )
    clinica    = relationship("Clinica")
    medico     = relationship("Utilizador", foreign_keys=[medico_id])
    entidade   = relationship("Entidade", foreign_keys=[entidade_id])
    itens      = relationship("ConsultaItem", back_populates="consulta")
    faturas    = relationship(
        "Fatura", 
        back_populates="consulta",
        cascade="all, delete-orphan"
    )


class ConsultaItem(Base):
    __tablename__ = "ConsultaItens"

    id              = Column(Integer, primary_key=True, index=True)
    consulta_id     = Column(Integer, ForeignKey("Consultas.id"), nullable=False)
    numero_dente    = Column(SmallInteger, nullable=True)
    face            = Column(ARRAY(Text), nullable=True, comment="Faces do dente: M, D, V, L, O, I")
    artigo_id       = Column(Integer, ForeignKey("Artigos.id"), nullable=False)
    quantidade      = Column(Integer, nullable=False, default=1)
    preco_unitario  = Column(Numeric(10,2), nullable=False)
    total           = Column(Numeric(12,2), nullable=False, default=0)

    consulta  = relationship("Consulta", back_populates="itens")
    artigo    = relationship("ArtigoMedico")
