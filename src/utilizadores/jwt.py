from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.config import settings
from src.utilizadores.models import Utilizador
from src.database import SessionLocal
from fastapi.security import OAuth2PasswordBearer


# Chave secreta (idealmente vem do .env)
SECRET_KEY = "supersegredo"  # substitui isto por uma variável de ambiente depois!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def create_access_token(data: dict, expires_delta: timedelta = None):
    """Gera um token JWT."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str):
    """Valida o token JWT e extrai os dados."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado.",
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
