from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from src.database import Base

class Auditoria(Base):
    __tablename__ = "Auditoria"
    id = Column(Integer, primary_key=True)
    utilizador_id = Column(Integer, ForeignKey("Utilizador.id"))
    acao = Column(String(100), nullable=False)  # Ex: "Atualização", "Criação", "Login"
    objeto = Column(String(100), nullable=False)  # Ex: "Utilizador", "Perfil", "Sessao"
    objeto_id = Column(Integer, nullable=True)    # ID do objeto afetado
    detalhes = Column(String(255))                # Texto livre, ex: "Nome alterado de X para Y"
    data = Column(DateTime, default=datetime.utcnow)

    utilizador = relationship("Utilizador")