from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from src.database import SessionLocal
from src.utilizadores.dependencies import get_current_user
from src.utilizadores.utils import is_master_admin
from src.utilizadores.models import Utilizador

from . import service, schemas, models, template
from fastapi.responses import JSONResponse


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

@router.put("/{ficha_id}", response_model=schemas.FichaClinicaResponse)
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
@router.post("/anotacoes", response_model=schemas.AnotacaoClinicaResponse)
def adicionar_anotacao(
    dados: schemas.AnotacaoClinicaCreate,
    db: Session = Depends(get_db),
    utilizador_atual: Utilizador = Depends(get_current_user),
):
    return service.adicionar_anotacao(db, dados, utilizador_atual.id)


# ---------- FICHEIRO ----------
@router.post("/ficheiros", response_model=schemas.FicheiroClinicoResponse)
def upload_ficheiro(
    dados: schemas.FicheiroClinicoCreate,
    db: Session = Depends(get_db),
    utilizador_atual: Utilizador = Depends(get_current_user),
):
    return service.upload_ficheiro_clinico(db, dados, utilizador_atual.id)


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
