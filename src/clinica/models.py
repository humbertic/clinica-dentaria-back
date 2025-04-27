from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from src.database import Base

class Clinica(Base):
    __tablename__ = "Clinica"
    id = Column(Integer, primary_key=True)
    nome = Column(String(100), nullable=False)
    email_envio = Column(String(100))
    morada = Column(Text)
    clinica_pai_id = Column(Integer, ForeignKey("Clinica.id"), nullable=True)
    partilha_dados = Column(Boolean, default=False)
    criado_por_id = Column(Integer, ForeignKey("Utilizador.id"), nullable=True)

    clinica_pai = relationship("Clinica", remote_side=[id])
    configuracoes = relationship("ClinicaConfiguracao", back_populates="clinica")
    emails = relationship("ClinicaEmail", back_populates="clinica")

class ClinicaConfiguracao(Base):
    __tablename__ = "ClinicaConfiguracao"
    id = Column(Integer, primary_key=True)
    clinica_id = Column(Integer, ForeignKey("Clinica.id"), nullable=True)
    chave = Column(String(100), nullable=False)
    valor = Column(Text, nullable=False)

    __table_args__ = (
        UniqueConstraint('clinica_id', 'chave', name='uix_clinica_id_chave'),
    )

    clinica = relationship("Clinica", back_populates="configuracoes")

class ClinicaEmail(Base):
    __tablename__ = "ClinicaEmail"
    id = Column(Integer, primary_key=True)
    clinica_id = Column(Integer, ForeignKey("Clinica.id"))
    remetente = Column(String(100))
    smtp_host = Column(String(100))
    smtp_porta = Column(Integer)
    utilizador_smtp = Column(String(100))
    password_smtp = Column(Text)
    ativo = Column(Boolean, default=True)

    clinica = relationship("Clinica", back_populates="emails")