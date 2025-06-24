from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from typing import List

from src.utilizadores import schemas, service, models
from src.database import SessionLocal
from src.utilizadores.jwt import create_access_token, refresh_access_token
from src.utilizadores.dependencies import get_current_user
from src.utilizadores.utils import is_master_admin
from datetime import datetime, timedelta
from fastapi import Request
from src.utilizadores.jwt import get_token_duration_for_user



router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Registro do Master Admin (primeiro utilizador)
@router.post("/registro", response_model=schemas.UtilizadorResponse)
def registrar(dados: schemas.UtilizadorCreate, db: Session = Depends(get_db)):
    if db.query(models.Utilizador).count() > 0:
        raise HTTPException(status_code=403, detail="Registo apenas permitido para o primeiro utilizador (Master Admin).")
    return service.criar_utilizador(db, dados, is_master_admin=True)

# Login (JWT)
@router.post("/login", response_model=schemas.TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Authenticate the user
    utilizador = service.autenticar_utilizador(
        db, 
        email_or_username=form_data.username, 
        password=form_data.password
    )
    
    # Get custom token duration based on user's clinics
    token_duration_minutes = get_token_duration_for_user(utilizador.id, db)
    
    # Create token with custom duration
    expires_delta = timedelta(minutes=token_duration_minutes)
    token = create_access_token(
        {"sub": str(utilizador.id)}, 
        expires_delta=expires_delta
    )
    
    # Record session in database
    expira_em = datetime.utcnow() + expires_delta
    service.criar_sessao(db, utilizador.id, token, expira_em)
    
    # Log the token duration for debugging
    print(f"Token created for user {utilizador.id} with duration of {token_duration_minutes} minutes")
    
    # Return the token response
    return {
        "access_token": token, 
        "token_type": "bearer",
        "expires_in": token_duration_minutes * 60  # Optional: Add seconds until expiration
    }

@router.post("/refresh-token", response_model=schemas.TokenResponse)
def refresh_token(
    request: Request,
    current_user: models.Utilizador = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Refresh the current user's access token.
    Requires a valid token to be present in the request headers.
    """
    old_token = get_token_from_request(request)
    
    session = db.query(models.Sessao).filter(
        models.Sessao.utilizador_id == current_user.id,
        models.Sessao.token == old_token,
        models.Sessao.ativo == True
    ).first()
    
    result = refresh_access_token(current_user.id, db)
    new_token = result["access_token"]
    
    token_duration_minutes = get_token_duration_for_user(current_user.id, db)
    nova_data_expiracao = datetime.utcnow() + timedelta(minutes=token_duration_minutes)
    
    if session:
        session.token = new_token
        session.data_expiracao = nova_data_expiracao
        db.commit()
    else:
        clinica_id = None
        user_clinica = db.query(models.UtilizadorClinica).filter(
            models.UtilizadorClinica.utilizador_id == current_user.id
        ).first()
        if user_clinica:
            clinica_id = user_clinica.clinica_id
            
        new_session = models.Sessao(
            utilizador_id=current_user.id,
            clinica_id=clinica_id,
            token=new_token,
            data_expiracao=nova_data_expiracao,
            ativo=True
        )
        db.add(new_session)
        db.commit()
    
    
    return result


def get_token_from_request(request: Request):
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token não fornecido.")
    return auth.split(" ")[1]

@router.post("/logout", response_model=dict)
def logout(
    request: Request,
    db: Session = Depends(get_db),
    utilizador_atual: models.Utilizador = Depends(get_current_user)
):
    token = get_token_from_request(request)
    return service.logout(db, utilizador_atual.id, token)

# Listar utilizadores (apenas Master Admin)
@router.get("", response_model=List[schemas.UtilizadorResponse])
def listar_utilizadores(
    db: Session = Depends(get_db),
    utilizador_atual: models.Utilizador = Depends(get_current_user)
):
    if not is_master_admin(utilizador_atual):
        raise HTTPException(status_code=403, detail="Apenas o Master Admin pode listar utilizadores.")
    return service.listar_utilizadores(db)


# Obter dados do próprio utilizador
@router.get("/me", response_model=schemas.UtilizadorResponse)
def obter_me(utilizador: models.Utilizador = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.obter_me(db, utilizador.id)

# Atualizar dados do próprio utilizador
@router.put("/me", response_model=schemas.UtilizadorResponse)
def atualizar_me(
    dados: schemas.UtilizadorUpdate,
    db: Session = Depends(get_db),
    utilizador: models.Utilizador = Depends(get_current_user)
):
    return service.atualizar_utilizador(db, utilizador.id, dados)

@router.post("/me/alterar-senha", response_model=dict)
def alterar_senha(
    req: schemas.AlterarSenhaRequest,
    db: Session = Depends(get_db),
    utilizador: models.Utilizador = Depends(get_current_user)
):
    return service.alterar_senha(db, utilizador.id, req.senha_atual, req.nova_senha)


@router.get(
    "/clinica/{clinica_id}/medicos",
    response_model=List[schemas.UtilizadorResponse],
    summary="Listar médicos de uma clínica",
)
def listar_medicos_clinica(
    clinica_id: int,
    db: Session = Depends(get_db),
    utilizador: models.Utilizador = Depends(get_current_user)
):
    """
    Retorna todos os utilizadores com perfil 'doctor' na clínica informada.
    """
    return service.listar_medicos_por_clinica(db, clinica_id)

# Obter utilizador por ID (apenas Master Admin)
@router.get("/{user_id}", response_model=schemas.UtilizadorResponse)
def obter_utilizador(
    user_id: int,
    db: Session = Depends(get_db),
    utilizador_atual: models.Utilizador = Depends(get_current_user)
):
    if not is_master_admin(utilizador_atual):
        raise HTTPException(status_code=403, detail="Apenas o Master Admin pode consultar utilizadores.")
    return service.obter_utilizador(db, user_id)

# Criar utilizador (apenas Master Admin)
@router.post("", response_model=schemas.UtilizadorResponse)
def criar_utilizador(
    dados: schemas.UtilizadorCreate,
    db: Session = Depends(get_db),
    utilizador_atual: models.Utilizador = Depends(get_current_user)
):
    if not is_master_admin(utilizador_atual):
        raise HTTPException(status_code=403, detail="Apenas o Master Admin pode criar utilizadores.")
    return service.criar_utilizador(db, dados, is_master_admin=False)

# Atualizar utilizador (apenas Master Admin)
@router.put("/{user_id}", response_model=schemas.UtilizadorResponse)
def atualizar_utilizador(
    user_id: int,
    dados: schemas.UtilizadorAdminUpdate,
    db: Session = Depends(get_db),
    utilizador_atual: models.Utilizador = Depends(get_current_user)
):
    if not is_master_admin(utilizador_atual):
        raise HTTPException(status_code=403, detail="Apenas o Master Admin pode atualizar utilizadores.")
    return service.admin_atualizar_utilizador(db, user_id, dados, utilizador_atual.id)

# Suspender utilizador (apenas Master Admin)
@router.post("/{user_id}/suspender", response_model=schemas.UtilizadorResponse)
def suspender_utilizador(
    user_id: int,
    db: Session = Depends(get_db),
    utilizador_atual: models.Utilizador = Depends(get_current_user)
):
    if not is_master_admin(utilizador_atual):
        raise HTTPException(status_code=403, detail="Apenas o Master Admin pode suspender utilizadores.")
    return service.suspender_utilizador(db, user_id, utilizador_atual.id)

# Ativar utilizador (apenas Master Admin)
@router.post("/{user_id}/ativar", response_model=schemas.UtilizadorResponse)
def ativar_utilizador(
    user_id: int,
    db: Session = Depends(get_db),
    utilizador_atual: models.Utilizador = Depends(get_current_user)
):
    if not is_master_admin(utilizador_atual):
        raise HTTPException(status_code=403, detail="Apenas o Master Admin pode ativar utilizadores.")
    return service.ativar_utilizador(db, user_id, utilizador_atual.id)



@router.post("/{user_id}/desbloquear", response_model=schemas.UtilizadorResponse)
def desbloquear_utilizador(
    user_id: int,
    db: Session = Depends(get_db),
    utilizador_atual: models.Utilizador = Depends(get_current_user)
):
    if not is_master_admin(utilizador_atual):
        raise HTTPException(status_code=403, detail="Apenas o Master Admin pode desbloquear utilizadores.")
    return service.desbloquear_utilizador(db, user_id, utilizador_atual.id)


@router.post("/{user_id}/perfis", response_model=dict)
def atribuir_perfil(
    user_id: int,
    req: schemas.AtribuirPerfilRequest,
    db: Session = Depends(get_db),
    utilizador_atual: models.Utilizador = Depends(get_current_user)
):
    if not is_master_admin(utilizador_atual):
        raise HTTPException(status_code=403, detail="Apenas o Master Admin pode atribuir perfis.")
    service.atribuir_perfil(db, user_id, req.perfil_id, utilizador_atual.id)
    return {"detail": "Perfil atribuído com sucesso."}

@router.delete("/{user_id}/perfis/{perfil_id}", response_model=dict)
def remover_perfil(
    user_id: int,
    perfil_id: int,
    db: Session = Depends(get_db),
    utilizador_atual: models.Utilizador = Depends(get_current_user)
):
    if not is_master_admin(utilizador_atual):
        raise HTTPException(status_code=403, detail="Apenas o Master Admin pode remover perfis.")
    return service.remover_perfil(db, user_id, perfil_id, utilizador_atual.id)

@router.post("/{user_id}/clinica", response_model=dict)
def atribuir_clinica(
    user_id: int,
    req: schemas.AtribuirClinicaRequest,
    db: Session = Depends(get_db),
    utilizador_atual: models.Utilizador = Depends(get_current_user)
):
    if not is_master_admin(utilizador_atual):
        raise HTTPException(status_code=403, detail="Apenas o Master Admin pode associar clínicas.")
    service.atribuir_clinicas(db, user_id, req.clinica_ids)
    return {"detail": "Clínicas associadas com sucesso."}