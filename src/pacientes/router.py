from fastapi import APIRouter, Depends, HTTPException, status, File, Form, UploadFile, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from src.database import SessionLocal
from src.utilizadores.dependencies import get_current_user
from src.utilizadores.utils import is_master_admin
from src.utilizadores.models import Utilizador
from src.consultas.schemas import ConsultaItemRead

from . import service, schemas, models, template
from fastapi.responses import JSONResponse,FileResponse
import os


router = APIRouter()


# ---------- DEPENDÊNCIA DB ----------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



@router.get(
    "/template",
    response_model=List[template.Pergunta],
    summary="Template do questionário (autenticado)",
    
)
def get_questionario_template():
    """
    Devolve o template do questionário de ficha clínica
    para o front-end renderizar dinamicamente o formulário.
    """
    return template.QUESTIONARIO

# ---------- PACIENTE ----------
@router.post(
    "",
    response_model=schemas.PacienteResponse,
    status_code=status.HTTP_201_CREATED,
)
def criar_paciente(
    dados: schemas.PacienteCreate,
    db: Session = Depends(get_db),
    utilizador_atual: Utilizador = Depends(get_current_user),
):
    """
    Recepcionista ou Master Admin pode registar novo paciente.  
    Cria automaticamente uma ficha clínica vazia (MVP).
    """
    # (exemplo simples → qualquer user autenticado pode criar;
    #   ajusta se quiseres restrições por perfil)
    paciente = service.criar_paciente(db, dados, utilizador_atual.id)

    # Criação automática da ficha clínica (TODO mover para consultas no futuro)
    service.criar_ficha_clinica(
        db,
        schemas.FichaClinicaCreate(paciente_id=paciente.id),
        utilizador_atual.id,
    )
    return paciente


@router.get(
    "",
    response_model=list[schemas.PacienteListItemResponse],
    summary="Listar pacientes da clínica"
)
def listar_pacientes_endpoint(
    clinica_id: int,
    db: Session = Depends(get_db),
    utilizador_atual: Utilizador = Depends(get_current_user),
):
    # (perm checks se precisares)
    return service.listar_pacientes(db, clinica_id)

@router.get("/search", response_model=list[schemas.PacienteMinimalResponse])
def buscar_pacientes_endpoint(
    q: str,
    clinica_id: Optional[int] = None,
    db: Session = Depends(get_db),
    utilizador_atual: Utilizador = Depends(get_current_user),
):
    """
    Busca pacientes pelo nome para uso em campos de autocompletar.
    """
    if len(q) < 2:
        return []
    return service.buscar_pacientes_por_nome(db, q, clinica_id)


@router.get("/{paciente_id}", response_model=schemas.PacienteResponse)
def obter_paciente_por_id(
    paciente_id: int,
    db: Session = Depends(get_db),
    utilizador_atual: Utilizador = Depends(get_current_user),
):
    return service.obter_paciente(db, paciente_id)


@router.put("/{paciente_id}", response_model=schemas.PacienteResponse)
def atualizar_paciente(
    paciente_id: int,
    dados: schemas.PacienteUpdate,
    db: Session = Depends(get_db),
    utilizador_atual: Utilizador = Depends(get_current_user),
):
    """
    Qualquer utilizador com permissão de receção ou master admin
    pode editar dados do paciente.
    """
    return service.atualizar_paciente(db, paciente_id, dados, utilizador_atual.id)


# ---------- FICHA CLÍNICA ----------




@router.post("", response_model=schemas.FichaClinicaResponse, status_code=status.HTTP_201_CREATED)
def criar_ficha_clinica(
    dados: schemas.FichaClinicaCreate,
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cria uma nova ficha clínica para o paciente.
    O responsável pela criação será o utilizador autenticado.
    """
    return service.criar_ficha_clinica(db, dados, user.id)


@router.get("/ficha/{ficha_id}", response_model=schemas.FichaClinicaResponse)
def ler_ficha_clinica(
    ficha_id: int,
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Recupera todos os dados da ficha clínica indicada.
    """
    ficha = service.obter_ficha(db, ficha_id)
    if not ficha:
        raise HTTPException(status_code=404, detail="Ficha clínica não encontrada.")
    return ficha

@router.put("/ficha/{ficha_id}", response_model=schemas.FichaClinicaResponse)
def atualizar_ficha_clinica(
    ficha_id: int,
    dados: schemas.FichaClinicaUpdate,
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Atualiza os campos da ficha clínica.
    Regista quem está a fazer a alteração.
    """
    ficha = service.atualizar_ficha_clinica(db, ficha_id, dados, user.id)
    if not ficha:
        raise HTTPException(status_code=404, detail="Ficha clínica não encontrada.")
    return ficha


# ---------- ANOTAÇÃO ----------
@router.post("/ficha/anotacoes", response_model=schemas.AnotacaoClinicaResponse)
def adicionar_anotacao(
    dados: schemas.AnotacaoClinicaCreate,
    db: Session = Depends(get_db),
    utilizador_atual: Utilizador = Depends(get_current_user),
):
    return service.adicionar_anotacao(db, dados, utilizador_atual.id)


# ---------- FICHEIRO ----------
@router.post("/ficha/ficheiros", response_model=schemas.FicheiroClinicoResponse)
def upload_ficheiro(
    ficha_id: int = Form(...),
    tipo: str = Form(...),
    ficheiro: UploadFile = File(...),
    db: Session = Depends(get_db),
    utilizador_atual: Utilizador = Depends(get_current_user),
):
    dados = schemas.FicheiroClinicoCreate(
        ficha_id=ficha_id,
        tipo=tipo,
        caminho_ficheiro=None  
    )
    
    return service.upload_ficheiro_clinico(db, dados, utilizador_atual.id, ficheiro)


@router.get("/ficha/ficheiros/{ficheiro_id}/view")
def view_ficheiro(
    ficheiro_id: int,
    db: Session = Depends(get_db),
    utilizador_atual: Utilizador = Depends(get_current_user),
):
    # Get the file record from the database
    ficheiro = db.query(models.FicheiroClinico).filter(models.FicheiroClinico.id == ficheiro_id).first()
    
    if not ficheiro:
        raise HTTPException(status_code=404, detail="Ficheiro não encontrado")
    
    # Check if the file exists on disk
    if not os.path.exists(ficheiro.caminho_ficheiro):
        raise HTTPException(status_code=404, detail="Arquivo físico não encontrado")
    
    # Determine the media type based on the file extension
    filename = os.path.basename(ficheiro.caminho_ficheiro)
    
    # Return the file as a response
    return FileResponse(
        path=ficheiro.caminho_ficheiro,
        filename=filename,
        # The media_type will be inferred from the file extension
    )


# ---------- PLANO DE TRATAMENTO ----------
@router.post("/planos", response_model=schemas.PlanoTratamentoResponse)
def criar_plano(
    dados: schemas.PlanoTratamentoCreate,
    db: Session = Depends(get_db),
    utilizador_atual: Utilizador = Depends(get_current_user),
):
    return service.criar_plano(db, dados, utilizador_atual.id)


@router.put("/planos/{plano_id}", response_model=schemas.PlanoTratamentoResponse)
def atualizar_plano(
    plano_id: int,
    dados: schemas.PlanoTratamentoUpdate,
    db: Session = Depends(get_db),
    utilizador_atual: Utilizador = Depends(get_current_user),
):
    return service.atualizar_plano(db, plano_id, dados, utilizador_atual.id)

@router.post("/planos/itens/{plano_item_id}/start", response_model=ConsultaItemRead)
def start_procedimento(
    plano_item_id: int,
    consulta_id: int,
    db: Session = Depends(get_db),
    utilizador_atual: Utilizador = Depends(get_current_user),
):
    return service.start_procedimento_from_plano(db, plano_item_id, consulta_id)

@router.get("/planos/completed", response_model=List[schemas.PlanoTratamentoDetailResponse])
def get_recently_completed_plans(
    paciente_id: int,
    hours: int = Query(1, description="How many hours back to look for completed plans"),
    db: Session = Depends(get_db),
    current_user: Utilizador = Depends(get_current_user)
):
    """
    Get plans that were recently completed for a patient
    """
    # Get raw results from service
    raw_results = service.get_recently_completed_plans(
        db=db, 
        paciente_id=paciente_id,
        hours=hours
    )
    
    if not raw_results:
        return []
    
    response_data = []
    for plan in raw_results:
        try:
            # Convert plan to dict
            plan_dict = {
                "id": plan.id,
                "paciente_id": plan.paciente_id,
                "estado": plan.estado,
                "data_criacao": plan.data_criacao,
                "data_conclusao": plan.data_conclusao,
                "descricao": getattr(plan, "descricao", ""), 
            }
            
            # Convert items
            items = []
            if hasattr(plan, "itens") and plan.itens:
                for item in plan.itens:
                    item_dict = {
                        "id": item.id,
                        "plano_id": item.plano_id,
                        "artigo_id": item.artigo_id,
                        "quantidade_prevista": item.quantidade_prevista,
                        "quantidade_executada": getattr(item, "quantidade_executada", 0),
                        "estado": item.estado,
                        "numero_dente": getattr(item, "numero_dente", None),
                        "face": getattr(item, "face", None),
                    }
                    items.append(item_dict)
            
            plan_dict["itens"] = items
            response_data.append(plan_dict)
            
        except Exception as e:
            print(f"Error converting plan to dict: {e}")
    
    return response_data

@router.get("/planos/{paciente_id}/plano-ativo", response_model=schemas.PlanoTratamentoDetailResponse)
def get_plano_ativo(
    paciente_id: int,
    db: Session = Depends(get_db),
    utilizador_atual: Utilizador = Depends(get_current_user),
):
    """
    Obtém o plano de tratamento ativo para um paciente específico.
    """
    # Verificar se o paciente existe
    paciente = service.obter_paciente(db, paciente_id)
    
    # Obter o plano ativo
    plano = service.obter_plano_ativo(db, paciente_id)
    
    if not plano:
        raise HTTPException(
            status_code=404, 
            detail="Não foi encontrado um plano de tratamento ativo para este paciente."
        )
    
    return plano