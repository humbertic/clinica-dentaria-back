from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, selectinload

from src.precos.models import Preco
from src.pacientes import models, schemas
from src.auditoria.utils import registrar_auditoria
from sqlalchemy import func
from src.consultas.models import Consulta, ConsultaItem
from datetime import datetime
import os
import uuid
import shutil
from fastapi import UploadFile



# -------------------------------------------------
# --------- PACIENTE ------------------------------
# -------------------------------------------------
def criar_paciente(
    db: Session,
    dados: schemas.PacienteCreate,
    utilizador_id: int
) -> models.Paciente:
    if dados.telefone and db.query(models.Paciente).filter_by(telefone=dados.telefone).first():
        raise HTTPException(status_code=400, detail="Telefone já registado.")
    if dados.email and db.query(models.Paciente).filter_by(email=dados.email).first():
        raise HTTPException(status_code=400, detail="E-mail já registado.")
    if dados.nif and db.query(models.Paciente).filter_by(nif=dados.nif).first():
        raise HTTPException(status_code=400, detail="NIF já registado.")

    paciente = models.Paciente(**dados.dict())
    db.add(paciente)
    db.commit()
    db.refresh(paciente)

    registrar_auditoria(
        db,
        utilizador_id,
        "Criação",
        "Paciente",
        paciente.id,
        f"Paciente '{paciente.nome}' criado."
    )
    return paciente



def listar_pacientes(db: Session, clinica_id: int):
    """
    Lista todos os pacientes de uma clínica com informações resumidas:
    - Total de consultas
    - Número de planos ativos
    - Indicação se tem ficha clínica
    - Próxima consulta agendada
    """
   
    
    # Buscar pacientes da clínica
    pacientes = (
        db.query(models.Paciente)
          .options(selectinload(models.Paciente.clinica))
          .filter_by(clinica_id=clinica_id)
          .order_by(models.Paciente.nome)
          .all()
    )
    
    # Enriquecer com dados derivados
    for paciente in pacientes:
        # Contar consultas
        paciente.total_consultas = (
            db.query(func.count(Consulta.id))
            .filter(Consulta.paciente_id == paciente.id)
            .scalar() or 0
        )
        
        # Contar planos ativos
        paciente.planos_ativos = (
            db.query(func.count(models.PlanoTratamento.id))
            .filter(
                models.PlanoTratamento.paciente_id == paciente.id,
                models.PlanoTratamento.estado == "em_curso"
            )
            .scalar() or 0
        )
        
        # Verificar se tem ficha clínica
        paciente.tem_ficha_clinica = (
            db.query(models.FichaClinica)
            .filter(models.FichaClinica.paciente_id == paciente.id)
            .first() is not None
        )
        
        # Buscar próxima consulta
        paciente.proxima_consulta = (
            db.query(Consulta)
            .filter(
                Consulta.paciente_id == paciente.id,
                Consulta.estado == "agendada",
                Consulta.data_inicio > datetime.now()
            )
            .order_by(Consulta.data_inicio)
            .first()
        )
    
    return pacientes

def obter_paciente(db: Session, paciente_id: int) -> models.Paciente:
    """
    Recupera um paciente pelo ID com todas as suas relações:
    - Fichas clínicas com anotações e ficheiros
    - Planos de tratamento com itens
    - Consultas com itens
    - Próxima consulta agendada
    """
    
    paciente = (
        db.query(models.Paciente)
          .options(
              # Fichas clínicas e seus relacionamentos
              selectinload(models.Paciente.fichas)
                .selectinload(models.FichaClinica.anotacoes),
              selectinload(models.Paciente.fichas)
                .selectinload(models.FichaClinica.ficheiros),
              # Planos de tratamento e seus itens
              selectinload(models.Paciente.planos)
                .selectinload(models.PlanoTratamento.itens)
                .selectinload(models.PlanoItem.artigo),
              # Consultas e seus relacionamentos
              selectinload(models.Paciente.consultas)
                .selectinload(Consulta.medico), 
              selectinload(models.Paciente.consultas)
                .selectinload(Consulta.entidade), 
              selectinload(models.Paciente.consultas)
                .selectinload(Consulta.itens)
                .selectinload(ConsultaItem.artigo),
              
              # Clínica
              selectinload(models.Paciente.clinica)
          )
          .filter(models.Paciente.id == paciente_id)
          .first()
    )
    
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente não encontrado.")
    
    procedimentos_historico = []

    for plano in paciente.planos:
        # Adicionar descrição ao plano
        setattr(plano, 'descricao', f"Plano de tratamento #{plano.id}")
        
        # Adicionar campos virtuais aos itens do plano
        for item in plano.itens:
            if item.artigo:
                # Garantir que o artigo tenha nome e código corretos
                if not hasattr(item.artigo, 'descricao') or not item.artigo.descricao:
                    setattr(item.artigo, 'descricao', f"Artigo {item.artigo.id}")
                if not hasattr(item.artigo, 'codigo') or not item.artigo.codigo:
                    setattr(item.artigo, 'codigo', f"COD-{item.artigo.id}")
    
    # Adicionar campos virtuais às consultas e processar os itens
    for consulta in paciente.consultas:
        # Garantir que médico e entidade tenham atributos de nome
        if consulta.medico and (not hasattr(consulta.medico, 'nome') or not consulta.medico.nome):
            setattr(consulta.medico, 'nome', f"Médico {consulta.medico.id}")
        if consulta.entidade and (not hasattr(consulta.entidade, 'nome') or not consulta.entidade.nome):
            setattr(consulta.entidade, 'nome', f"Entidade {consulta.entidade.id}")
        
        # Processar itens da consulta
        if hasattr(consulta, 'itens') and consulta.itens:
            for item in consulta.itens:
                # Adicionar informações do artigo ao item da consulta
                if hasattr(item, 'artigo') and item.artigo:
                    # Garantir que o artigo tenha descrição
                    if not hasattr(item.artigo, 'descricao') or not item.artigo.descricao:
                        setattr(item.artigo, 'descricao', f"Artigo {item.artigo.id}")
                    if not hasattr(item.artigo, 'codigo') or not item.artigo.codigo:
                        setattr(item.artigo, 'codigo', f"COD-{item.artigo.id}")
                    
                    # Adicionar atributos diretamente ao item para facilitar serialização
                    setattr(item, 'artigo_descricao', item.artigo.descricao)
                    setattr(item, 'artigo_codigo', item.artigo.codigo)
                else:
                    # Se o artigo não estiver carregado, obter diretamente do banco
                    from src.artigos.models import Artigo
                    artigo = db.query(Artigo).filter_by(id=item.artigo_id).first()
                    if artigo:
                        setattr(item, 'artigo_descricao', artigo.descricao)
                        setattr(item, 'artigo_codigo', artigo.codigo)
                    else:
                        setattr(item, 'artigo_descricao', f"Artigo {item.artigo_id}")
                        setattr(item, 'artigo_codigo', f"COD-{item.artigo_id}")
                
                # Para consultas concluídas, também adicionar ao histórico de procedimentos
                if consulta.estado == "concluida":
                    procedimento = {
                        'id': item.id,
                        'consulta_id': consulta.id,
                        'consulta_data': consulta.data_inicio.isoformat() if consulta.data_inicio else None,
                        'artigo_id': item.artigo_id,
                        'artigo_descricao': getattr(item, 'artigo_descricao', f"Artigo {item.artigo_id}"),
                        'artigo_codigo': getattr(item, 'artigo_codigo', f"COD-{item.artigo_id}"),
                        'numero_dente': item.numero_dente,
                        'face': item.face,
                        'total': item.total,
                        'medico_id': consulta.medico_id,
                        'medico_nome': getattr(consulta.medico, 'nome', f"Médico {consulta.medico_id}") if consulta.medico else None
                    }
                    procedimentos_historico.append(procedimento)
    
    # Ordenar histórico de procedimentos por data, mais recente primeiro
    procedimentos_historico.sort(
        key=lambda x: x['consulta_data'] if x['consulta_data'] else "", 
        reverse=True
    )
    
    # Adicionar o histórico de procedimentos ao objeto do paciente
    setattr(paciente, 'procedimentos_historico', procedimentos_historico)
    
    return paciente
    


def buscar_pacientes_por_nome(db: Session, nome_parcial: str, clinica_id: Optional[int] = None):
    """
    Busca pacientes cujo nome contenha o termo de busca.
    Opcionalmente filtra por clínica.
    """
    query = db.query(models.Paciente).filter(
        models.Paciente.nome.ilike(f"%{nome_parcial}%")
    )
    
    if clinica_id is not None:
        query = query.filter(models.Paciente.clinica_id == clinica_id)
    
    return query.order_by(models.Paciente.nome).limit(10).all()

def obter_ficha_por_paciente(db: Session, paciente_id: int) -> Optional[models.FichaClinica]:
    """
    Obtém a ficha clínica de um paciente, se existir.
    """
    return (
        db.query(models.FichaClinica)
          .options(
              selectinload(models.FichaClinica.anotacoes),
              selectinload(models.FichaClinica.ficheiros)
          )
          .filter(models.FichaClinica.paciente_id == paciente_id)
          .first()
    )


def atualizar_paciente(
    db: Session,
    paciente_id: int,
    dados: schemas.PacienteUpdate,
    utilizador_id: int
) -> models.Paciente:
    paciente = obter_paciente(db, paciente_id)

    for campo, valor in dados.dict(exclude_unset=True).items():
        setattr(paciente, campo, valor)

    db.commit()
    db.refresh(paciente)

    registrar_auditoria(
        db,
        utilizador_id,
        "Atualização",
        "Paciente",
        paciente_id,
        f"Paciente '{paciente.nome}' atualizado."
    )
    return paciente


# -------------------------------------------------
# --------- FICHA CLÍNICA -------------------------
# -------------------------------------------------
def criar_ficha_clinica(
    db: Session,
    dados: schemas.FichaClinicaCreate,
    utilizador_id: int
) -> models.FichaClinica:
    ficha = models.FichaClinica(**dados.dict(), responsavel_criacao_id=utilizador_id)
    db.add(ficha)
    db.commit()
    db.refresh(ficha)

    registrar_auditoria(
        db,
        utilizador_id,
        "Criação",
        "FichaClinica",
        ficha.id,
        f"Ficha clínica criada para paciente {ficha.paciente_id}."
    )
    return ficha


def obter_ficha(db: Session, ficha_id: int) -> models.FichaClinica:
    """
    Recupera uma ficha clínica pelo seu ID.
    Levanta 404 se não existir.
    """
    ficha = (
        db.query(models.FichaClinica)
          .options(
              selectinload(models.FichaClinica.paciente),
              selectinload(models.FichaClinica.anotacoes),
              selectinload(models.FichaClinica.ficheiros),
          )
          .filter(models.FichaClinica.id == ficha_id)
          .first()
    )
    if not ficha:
        raise HTTPException(status_code=404, detail="Ficha clínica não encontrada.")
    return ficha


def atualizar_ficha_clinica(
    db: Session,
    ficha_id: int,
    dados: schemas.FichaClinicaUpdate,
    utilizador_id: int
) -> models.FichaClinica:
    """
    Atualiza os campos de uma ficha clínica existente.
    Só altera os campos definidos em dados.
    Regista auditoria do update.
    """
    ficha = db.query(models.FichaClinica).filter_by(id=ficha_id).first()
    if not ficha:
        raise HTTPException(status_code=404, detail="Ficha clínica não encontrada.")

    # aplica apenas os campos enviados
    for campo, valor in dados.dict(exclude_unset=True).items():
        setattr(ficha, campo, valor)

    # atualiza quem e quando
    ficha.responsavel_atualizacao_id = utilizador_id

    db.commit()
    db.refresh(ficha)

    registrar_auditoria(
        db,
        utilizador_id,
        "Atualização",
        "FichaClinica",
        ficha.id,
        f"Ficha clínica {ficha.id} atualizada."
    )
    return ficha


def adicionar_anotacao(
    db: Session,
    dados: schemas.AnotacaoClinicaCreate,
    utilizador_id: int
) -> models.AnotacaoClinica:
    # verifica se ficha existe
    ficha = db.query(models.FichaClinica).filter_by(id=dados.ficha_id).first()
    if not ficha:
        raise HTTPException(status_code=404, detail="Ficha clínica não encontrada.")

    anot = models.AnotacaoClinica(**dados.dict())
    db.add(anot)
    db.commit()
    db.refresh(anot)

    registrar_auditoria(
        db,
        utilizador_id,
        "Criação",
        "AnotacaoClinica",
        anot.id,
        f"Anotação adicionada à ficha {dados.ficha_id}."
    )
    return anot


def upload_ficheiro_clinico(
    db: Session,
    dados: schemas.FicheiroClinicoCreate,
    utilizador_id: int,
    ficheiro: UploadFile = None  
) -> models.FicheiroClinico:
    """
    Saves a clinical file and creates a database record.
    
    This function can handle two scenarios:
    1. Direct file upload: When ficheiro is provided, it saves the file and creates a record
    2. Path-based: When caminho_ficheiro is provided in dados, it just creates a record
    """
    # If a file was uploaded, save it and update the path
    if ficheiro:
        # Create uploads directory if it doesn't exist
        upload_dir = "uploads/ficheiros"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Create a unique filename to avoid collisions
        filename = f"{uuid.uuid4()}_{ficheiro.filename}"
        file_path = os.path.join(upload_dir, filename)
        
        # Save the uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(ficheiro.file, buffer)
        
        # Update the path in dados
        dados.caminho_ficheiro = file_path
    
    # Create and save the database record
    ficheiro_db = models.FicheiroClinico(**dados.dict())
    db.add(ficheiro_db)
    db.commit()
    db.refresh(ficheiro_db)

    registrar_auditoria(
        db,
        utilizador_id,
        "Upload",
        "FicheiroClinico",
        ficheiro_db.id,
        f"Ficheiro '{ficheiro_db.tipo}' anexado à ficha {dados.ficha_id}."
    )
    return ficheiro_db


# -------------------------------------------------
# --------- PLANO DE TRATAMENTO -------------------
# -------------------------------------------------
def criar_plano(
    db: Session,
    dados: schemas.PlanoTratamentoCreate,
    utilizador_id: int
) -> models.PlanoTratamento:
    plano = models.PlanoTratamento(**dados.dict(), estado="em_curso")
    db.add(plano)
    db.commit()
    db.refresh(plano)

    registrar_auditoria(
        db,
        utilizador_id,
        "Criação",
        "PlanoTratamento",
        plano.id,
        f"Plano de tratamento criado para paciente {plano.paciente_id}."
    )
    return plano


def atualizar_plano(
    db: Session,
    plano_id: int,
    dados: schemas.PlanoTratamentoUpdate,
    utilizador_id: int
) -> models.PlanoTratamento:
    plano = db.query(models.PlanoTratamento).filter_by(id=plano_id).first()
    if not plano:
        raise HTTPException(status_code=404, detail="Plano não encontrado.")

    for campo, valor in dados.dict(exclude_unset=True).items():
        setattr(plano, campo, valor)

    db.commit()
    db.refresh(plano)

    registrar_auditoria(
        db,
        utilizador_id,
        "Atualização",
        "PlanoTratamento",
        plano_id,
        f"Plano de tratamento {plano_id} atualizado."
    )
    return plano



def obter_plano_ativo(db: Session, paciente_id: int) -> Optional[models.PlanoTratamento]:
    """
    Obtém o plano de tratamento ativo (em_curso) para um determinado paciente.
    Retorna None se não houver plano ativo.
    """
    return (
        db.query(models.PlanoTratamento)
          .options(
              selectinload(models.PlanoTratamento.itens)
                .selectinload(models.PlanoItem.artigo)
          )
          .filter(
              models.PlanoTratamento.paciente_id == paciente_id,
              models.PlanoTratamento.estado == "em_curso"
          )
          .order_by(models.PlanoTratamento.data_criacao.desc())  # Obtém o mais recente
          .first()
    )


def start_procedimento_from_plano(
    db: Session,
    plano_item_id: int,
    consulta_id: int
) -> ConsultaItem:
    """
    Starts a procedure from a treatment plan by:
    1. Updating the status of the PlanoItem to 'em_andamento'
    2. Creating a ConsultaItem in the current consultation with properties from PlanoItem
    3. If all items are completed, also marks the entire plan as completed
    
    Args:
        db: Database session
        plano_item_id: ID of the PlanoItem to start
        consulta_id: ID of the current Consulta where the procedure will be performed
        
    Returns:
        The created ConsultaItem
        
    Raises:
        HTTPException: If item or consultation not found, or if invalid state
    """
    plano_item = db.query(models.PlanoItem).filter_by(id=plano_item_id).first()
    if not plano_item:
        raise HTTPException(
            status_code=404, 
            detail=f"Item do plano de tratamento com ID={plano_item_id} não encontrado."
        )
    
    if plano_item.estado in ("concluido", "cancelado"):
        raise HTTPException(
            status_code=400,
            detail=f"Este procedimento já está {plano_item.estado} e não pode ser iniciado."
        )
    
    consulta = db.query(Consulta).filter_by(id=consulta_id).first()
    if not consulta:
        raise HTTPException(
            status_code=404,
            detail=f"Consulta com ID={consulta_id} não encontrada."
        )
    
    if consulta.estado not in ("iniciada", "em_andamento"):
        raise HTTPException(
            status_code=400,
            detail=f"A consulta está {consulta.estado} e não permite adicionar procedimentos."
        )
    
    preco = (
        db.query(Preco)
          .filter_by(
              artigo_id=plano_item.artigo_id,
              entidade_id=consulta.entidade_id
          )
          .first()
    )
    
    if not preco:
        raise HTTPException(
            status_code=500,
            detail="Preço para este artigo e entidade não encontrado."
        )
    
    valor_unit = float(preco.valor_paciente)
    quantidade = 1
    total = quantidade * valor_unit
    
    consulta_item = ConsultaItem(
        consulta_id=consulta.id,
        artigo_id=plano_item.artigo_id,
        quantidade=quantidade,
        preco_unitario=valor_unit,
        total=total,
        numero_dente=plano_item.numero_dente,
        face=plano_item.face,
    )
    
    plano_item.estado = "concluido"
    plano_item.quantidade_executada += 1
    
    plano = db.query(models.PlanoTratamento).filter_by(id=plano_item.plano_id).first()
    
    all_items_completed = True
    for item in plano.itens:
        if item.estado != "concluido" and item.estado != "cancelado":
            all_items_completed = False
            break
    
    if all_items_completed and plano.estado != "concluido":
        plano.estado = "concluido"
        plano.data_conclusao = datetime.now()
        
        registrar_auditoria(
            db,
            consulta.medico_id, 
            "Conclusão",
            "PlanoTratamento",
            plano.id,
            f"Plano de tratamento {plano.id} concluído automaticamente."
        )
    
    db.add(consulta_item)
    db.commit()
    db.refresh(consulta_item)
    
    return consulta_item

def get_recently_completed_plans(
    db: Session, 
    paciente_id: int,
    hours: int = 1
) -> List[models.PlanoTratamento]:
    """
    Get treatment plans that were recently completed for a specific patient.
    
    Args:
        db: Database session
        paciente_id: ID of the patient
        hours: How many hours back to look for completed plans (default: 1)
        
    Returns:
        List of recently completed PlanoTratamento objects
    """
    cutoff_time = datetime.now() - timedelta(hours=hours)
    print(f"Cutoff time for completed plans: {cutoff_time.isoformat()}")
    print(f"Searching for completed plans for patient ID={paciente_id} since {cutoff_time.isoformat()}")
    return (
        db.query(models.PlanoTratamento)
          .filter(
              models.PlanoTratamento.paciente_id == paciente_id,
              models.PlanoTratamento.estado == "concluido",
              models.PlanoTratamento.data_conclusao >= cutoff_time
          )
          .order_by(models.PlanoTratamento.data_conclusao.desc())
          .all()
    )