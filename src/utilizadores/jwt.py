from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.config import settings
from src.utilizadores.models import Utilizador, UtilizadorClinica
from src.database import SessionLocal
from fastapi.security import OAuth2PasswordBearer
from src.clinica.models import Clinica, ClinicaConfiguracao
from sqlalchemy.orm import joinedload



# Chave secreta (idealmente vem do .env)
SECRET_KEY = "supersegredo"  # substitui isto por uma variável de ambiente depois!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def get_token_duration_for_user(user_id: int, db: Session) -> int:
    """
    Get the token duration in minutes for a user based on their clinics.
    
    The logic is:
    1. Get all clinics associated with the user through UtilizadorClinica table
    2. For each clinic, check if it has a parent clinic
    3. Get the token duration config from the clinic or its parent
    4. Return the first valid duration found (parent clinics prioritized)
    
    Returns default duration if no configuration is found.
    """
    default_duration = ACCESS_TOKEN_EXPIRE_MINUTES
    
    
    user_clinicas = db.query(UtilizadorClinica).filter(
        UtilizadorClinica.utilizador_id == user_id
    ).all()
    
    if not user_clinicas:
        print(f"No clinics found for user {user_id}, using default duration {default_duration}")
        return default_duration
    
    clinic_ids = [uc.clinica_id for uc in user_clinicas]
    
    clinics = db.query(Clinica).filter(Clinica.id.in_(clinic_ids)).all()
    
    parent_clinic_ids = []
    direct_clinic_ids = []
    
    for clinic in clinics:
        if clinic.clinica_pai_id:
            parent_clinic_ids.append(clinic.clinica_pai_id)
        else:
            direct_clinic_ids.append(clinic.id)
    
    all_clinic_ids = parent_clinic_ids + direct_clinic_ids
    
    if not all_clinic_ids:
        print(f"No valid clinic IDs found for user {user_id}, using default duration {default_duration}")
        return default_duration
    
    configs = db.query(ClinicaConfiguracao).filter(
        ClinicaConfiguracao.clinica_id.in_(all_clinic_ids),
        ClinicaConfiguracao.chave == "tempo_duracao_token"
    ).all()
    
    if not configs:
        print(f"No token duration configs found for clinics {all_clinic_ids}, using default duration {default_duration}")
        return default_duration
    
    durations_by_clinic = {}
    for config in configs:
        try:
            durations_by_clinic[config.clinica_id] = int(config.valor)
        except (ValueError, TypeError):
            print(f"Invalid token duration value in config: {config.valor}")
    
    for clinic_id in all_clinic_ids:
        if clinic_id in durations_by_clinic:
            duration = durations_by_clinic[clinic_id]
            print(f"Using token duration {duration} minutes from clinic {clinic_id}")
            return duration
    
    print(f"No valid duration found in configs, using default duration {default_duration}")
    return default_duration





def create_access_token(data: dict, db: Session = None, user_id: int = None, expires_delta: timedelta = None):
    """
    Generates a JWT with dynamic expiration based on user's clinic configuration.
    
    Args:
        data: The payload to encode in the token
        db: Database session for looking up clinic configuration
        user_id: ID of the user to check for custom token duration
        expires_delta: Optional override for token expiration
    """
    to_encode = data.copy()
    
    # If explicit expiration is provided, use it
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    # Otherwise, if we have a DB session and user ID, look up custom duration
    elif db and user_id:
        # Get custom duration from clinic configuration
        minutes = get_token_duration_for_user(user_id, db)
        expire = datetime.utcnow() + timedelta(minutes=minutes)
    # Fall back to default expiration
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str):
    """Validates JWT token and extracts data."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado. Por favor, faça login novamente.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou malformado.",
            headers={"WWW-Authenticate": "Bearer"},
        )


# Dependência para obter utilizador atual
def get_current_user(token: str = Depends(lambda: get_bearer_token()), db: Session = Depends(lambda: SessionLocal())):
    payload = verify_token(token)
    user_id = int(payload.get("sub"))
    utilizador = db.query(Utilizador).filter(Utilizador.id == user_id).first()
    if not utilizador or not utilizador.ativo:
        raise HTTPException(status_code=403, detail="Utilizador não encontrado ou inativo.")
    return utilizador


# Função auxiliar para extrair o token da autorização
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/utilizadores/login")

def get_bearer_token(token: str = Depends(oauth2_scheme)):
    return token


def refresh_access_token(user_id: int, db: Session) -> dict:
    """
    Creates a new access token for an existing user.
    Used for refreshing sessions without requiring a new login.
    
    Args:
        user_id: The ID of the user to refresh the token for
        db: Database session for looking up user and clinic configuration
        
    Returns:
        dict: A dictionary containing the new token and expiration info
    """
    # Verify user exists and is active
    user = db.query(Utilizador).filter(Utilizador.id == user_id).first()
    if not user or not user.ativo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilizador não encontrado ou inativo."
        )
    
    data = {"sub": str(user_id)}
    token = create_access_token(data=data, db=db, user_id=user_id)
    
    duration_minutes = get_token_duration_for_user(user_id, db)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": duration_minutes * 60  
    }