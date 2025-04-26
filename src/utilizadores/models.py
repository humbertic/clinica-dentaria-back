from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, TIMESTAMP
from sqlalchemy.orm import relationship
from src.perfis.models import Perfil
from src.database import Base


class Utilizador(Base):
    __tablename__ = "Utilizador"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    nome = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    telefone = Column(String(20), unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    ativo = Column(Boolean, default=True)
    tentativas_falhadas = Column(Integer, default=0)
    bloqueado = Column(Boolean, default=False)

    perfis = relationship("UtilizadorClinica", back_populates="utilizador")
    sessoes = relationship("Sessao", back_populates="utilizador")



class UtilizadorClinica(Base):
    __tablename__ = "UtilizadorClinica"

    id = Column(Integer, primary_key=True)
    utilizador_id = Column(Integer, ForeignKey("Utilizador.id"))
    clinica_id = Column(Integer, ForeignKey("Clinica.id"))  # Now a real FK!
    perfil_id = Column(Integer, ForeignKey("Perfil.id"))
    ativo = Column(Boolean, default=True)

    utilizador = relationship("Utilizador", back_populates="perfis")
    perfil = relationship("Perfil")
    clinica = relationship("Clinica")  


class Sessao(Base):
    __tablename__ = "Sessao"

    id = Column(Integer, primary_key=True)
    utilizador_id = Column(Integer, ForeignKey("Utilizador.id"))
    clinica_id = Column(Integer, ForeignKey("Clinica.id"))  # Now a real FK!
    token = Column(Text, nullable=False)
    data_expiracao = Column(TIMESTAMP)
    ativo = Column(Boolean, default=True)

    utilizador = relationship("Utilizador", back_populates="sessoes")
    clinica = relationship("Clinica")  # Add this line
