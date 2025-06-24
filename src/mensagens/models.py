from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Index
)
from sqlalchemy.orm import relationship
from src.database import Base


class Thread(Base):
    __tablename__ = "Threads"
    __table_args__ = (
        # Unique constraint for DMs between two users
        Index(
            "ix_threads_pair_clinica",
            "clinica_id", "participante_a_id", "participante_b_id",
            unique=True
        ),
    )

    id = Column(Integer, primary_key=True)
    clinica_id = Column(Integer, ForeignKey("Clinica.id"), nullable=False)
    # For direct messages between two users
    participante_a_id = Column(Integer, ForeignKey("Utilizador.id"), nullable=True)
    participante_b_id = Column(Integer, ForeignKey("Utilizador.id"), nullable=True)
    # For clinic-wide or group chats
    nome = Column(String(50), nullable=True)  # Optional name for the chat
    tipo = Column(String(20), default="dm")  # "dm", "clinic", "group"
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    clinica = relationship("Clinica")
    participante_a = relationship("Utilizador", foreign_keys=[participante_a_id])
    participante_b = relationship("Utilizador", foreign_keys=[participante_b_id])
    mensagens = relationship("Mensagem", back_populates="thread",
                             order_by="Mensagem.created_at")


class Mensagem(Base):
    __tablename__ = "Mensagens"

    id           = Column(Integer, primary_key=True)
    clinica_id   = Column(Integer, ForeignKey("Clinica.id"), nullable=False)
    thread_id    = Column(Integer, ForeignKey("Threads.id"))
    remetente_id = Column(Integer, ForeignKey("Utilizador.id"), nullable=False)
    texto        = Column(Text, nullable=False)
    created_at   = Column(DateTime, default=datetime.utcnow)
    lida         = Column(Boolean, default=False)

    thread       = relationship("Thread", back_populates="mensagens")
    clinica      = relationship("Clinica")