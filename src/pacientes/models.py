from sqlalchemy import (
    ARRAY,
    Column,
    Integer,
    SmallInteger,
    String,
    Text,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    func,
)
from sqlalchemy.orm import relationship
from src.database import Base

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Date,
    DateTime,
    ForeignKey,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB


# ---------- PACIENTE ----------
class Paciente(Base):
    __tablename__ = "Paciente"

    id = Column(Integer, primary_key=True)
    clinica_id = Column(Integer, ForeignKey("Clinica.id"), nullable=False)
    nome = Column(String(100), nullable=False)
    nif = Column(String(20), unique=True, nullable=True)
    data_nascimento = Column(Date)
    sexo = Column(String(10))                  # M / F / Outro
    nacionalidade = Column(String(50))           # nacionalidade
    tipo_documento = Column(String(50))          # tipo de documento (ex: CC, passaporte, etc.)
    numero_documento = Column(String(50), unique=True)  # número do documento
    validade_documento = Column(Date, nullable=True) # validade do documento
    telefone = Column(String(20), unique=True)
    email = Column(String(100), unique=True)
    pais_residencia = Column(String(50))            # país de residência
    morada = Column(String(200))                    # morada

    # — Relacionamentos
    fichas = relationship(
        "FichaClinica",
        back_populates="paciente",
        cascade="all, delete-orphan",
    )
    planos = relationship(
        "PlanoTratamento",
        back_populates="paciente",
        cascade="all, delete-orphan",
    )
    
    clinica = relationship(
        "Clinica",
        backref="pacientes",
        lazy="joined",           # joined-load por omissão
    )
    consultas = relationship(
        "Consulta", 
        back_populates="paciente",
        lazy="select"
    )
    faturas = relationship(
        "Fatura",
        back_populates="paciente",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:  # type: ignore[override]
        return f"<Paciente {self.id} - {self.nome}>"

# src/pacientes/models.py



class FichaClinica(Base):
    __tablename__ = "FichaClinica"

    id = Column(Integer, primary_key=True)
    paciente_id = Column(Integer, ForeignKey("Paciente.id"), nullable=False)
    data_criacao = Column(DateTime, server_default=func.now())

    # --- Dados do cabeçalho do questionário ---
    estado_civil        = Column(String(50),  nullable=True)
    profissao           = Column(String(100), nullable=True)
    endereco            = Column(Text,        nullable=True)
    telefone            = Column(String(20),  nullable=True)
    local_trabalho      = Column(String(100), nullable=True)
    telefone_trabalho   = Column(String(20),  nullable=True)
    tipo_beneficiario   = Column(String(50),  nullable=True)
    numero_beneficiario = Column(String(50),  nullable=True)
    recomendado_por     = Column(String(100), nullable=True)
    data_questionario   = Column(Date,        nullable=True)

    # --- Queixa principal ---
    queixa_principal    = Column(Text,        nullable=True)

    # --- História Médica e Odontológica (sim/não + detalhes em JSON) ---
    historia_medica     = Column(
        JSONB,
        nullable=True,
        comment="Respostas às perguntas de História Médica e Odontológica"
    )

    # --- Exame Clínico (Extra/Intra bucal) ---
    exame_clinico       = Column(Text, nullable=True)

    # --- Plano Geral de Tratamento (mapa dentário, anotações por dente em JSON) ---
    plano_geral         = Column(
        JSONB,
        nullable=True,
        comment="Mapa dentário e anotações por dente"
    )

    # --- Observações finais livres ---
    observacoes_finais  = Column(Text, nullable=True)

    # --- Auditoria: quem criou e actualizou ---
    responsavel_criacao_id    = Column(Integer, ForeignKey("Utilizador.id"), nullable=False)
    responsavel_atualizacao_id = Column(Integer, ForeignKey("Utilizador.id"), nullable=True)
    data_atualizacao          = Column(DateTime, onupdate=func.now())

    # --- Relacionamentos ---
    paciente = relationship("Paciente", back_populates="fichas")
    anotacoes = relationship(
        "AnotacaoClinica",
        back_populates="ficha",
        cascade="all, delete-orphan",
    )
    ficheiros = relationship(
        "FicheiroClinico",
        back_populates="ficha",
        cascade="all, delete-orphan",
    )


# ---------- ANOTAÇÃO CLÍNICA ----------
class AnotacaoClinica(Base):
    __tablename__ = "AnotacaoClinica"

    id = Column(Integer, primary_key=True)
    ficha_id = Column(Integer, ForeignKey("FichaClinica.id"))
    consulta_id = Column(Integer, ForeignKey("Consultas.id"), nullable=True)   
    texto = Column(Text, nullable=False)
    data = Column(DateTime, server_default=func.now())

    ficha = relationship("FichaClinica", back_populates="anotacoes")
    consulta = relationship("Consulta", back_populates="anotacoes") 

# ---------- FICHEIRO CLÍNICO ----------
class FicheiroClinico(Base):
    __tablename__ = "FicheiroClinico"

    id = Column(Integer, primary_key=True)
    ficha_id = Column(Integer, ForeignKey("FichaClinica.id"))
    consulta_id = Column(Integer, ForeignKey("Consultas.id"), nullable=True)   
    tipo = Column(String(50))                         # radiografia, pdf, imagem, etc.
    caminho_ficheiro = Column(Text)
    data_upload = Column(DateTime, server_default=func.now())

    ficha = relationship("FichaClinica", back_populates="ficheiros")
    consulta = relationship("Consulta", back_populates="ficheiros")

# ---------- PLANO DE TRATAMENTO ----------
class PlanoTratamento(Base):
    __tablename__ = "PlanoTratamento"
    id              = Column(Integer, primary_key=True, index=True)
    paciente_id     = Column(Integer, ForeignKey("Paciente.id"), nullable=False)
    data_criacao    = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    estado          = Column(String(50), nullable=False, default="em_curso")
    data_conclusao  = Column(DateTime(timezone=True), nullable=True)

    paciente = relationship("Paciente", back_populates="planos")
    itens    = relationship("PlanoItem", back_populates="plano", cascade="all, delete-orphan")
    faturas = relationship(
        "Fatura",
        back_populates="plano",
        cascade="all, delete-orphan",
        uselist=False  # cada plano só pode ter uma fatura associada
    )

# ---------- LIGAÇÃO CONSULTA <-> PLANO ----------
# class ConsultaPlanoTratamento(Base):
#     __tablename__ = "ConsultaPlanoTratamento"

#     consulta_id = Column(Integer, ForeignKey("Consultas.id"), primary_key=True) 
#     plano_id = Column(Integer, ForeignKey("PlanoTratamento.id"), primary_key=True)

#     plano = relationship("PlanoTratamento", back_populates="consultas")
#     consulta = relationship("Consulta", back_populates="planos")  

class PlanoItem(Base):
    __tablename__ = "PlanoItem"
    id                 = Column(Integer, primary_key=True, index=True)
    plano_id           = Column(Integer, ForeignKey("PlanoTratamento.id"), nullable=False)
    orcamento_item_id  = Column(Integer, ForeignKey("OrcamentoItens.id"), nullable=False)
    artigo_id          = Column(Integer, ForeignKey("Artigos.id"),     nullable=False)

    quantidade_prevista    = Column(Integer, nullable=False)
    numero_dente           = Column(SmallInteger, nullable=True)
    face                   = Column(ARRAY(Text), nullable=True)

    quantidade_executada   = Column(Integer, nullable=False, default=0)
    estado                 = Column(String(20), nullable=False, default="pendente")

    plano           = relationship("PlanoTratamento", back_populates="itens")
    orcamento_item  = relationship("OrcamentoItem", lazy="joined")
    artigo          = relationship("ArtigoMedico",  lazy="joined")

