from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, Text, func
)
from sqlalchemy.orm import relationship
from src.database import Base

class Marcacao(Base):
    __tablename__ = "Marcacoes"

    id           = Column(Integer, primary_key=True, index=True)
    paciente_id  = Column(Integer, ForeignKey("Paciente.id"), nullable=False)
    medico_id    = Column(Integer, ForeignKey("Utilizador.id"), nullable=False)  
    clinic_id    = Column(Integer, ForeignKey("Clinica.id"), nullable=False)
    agendada_por = Column(Integer, ForeignKey("Utilizador.id"), nullable=False)  

    entidade_id  = Column(Integer, ForeignKey("Entidades.id"), nullable=False)
    observacoes  = Column(Text, nullable=True)

    data_hora_inicio = Column("data_hora_inicio", DateTime(timezone=True), nullable=False)
    data_hora_fim    = Column("data_hora_fim",    DateTime(timezone=True), nullable=False)
    titulo           = Column("titulo", String(200), nullable=False, default="Marcação")
    estado       = Column(String(20), nullable=False, default="agendada") # Estado padrão 'agendada', outros estados podem ser: falta, iniciada, concluida, cancelada

    created_at   = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at   = Column(DateTime(timezone=True), server_default=func.now(),
                          onupdate=func.now(), nullable=False)

    paciente     = relationship("Paciente")
    medico       = relationship("Utilizador", foreign_keys=[medico_id])      
    clinic       = relationship("Clinica")
    agendador    = relationship("Utilizador", foreign_keys=[agendada_por])  
    entidade     = relationship("Entidade")