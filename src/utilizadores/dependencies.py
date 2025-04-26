from datetime import datetime
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.utilizadores.jwt import verify_token
from src.utilizadores.models import Utilizador, Sessao
from src.database import SessionLocal
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/utilizadores/login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    payload = verify_token(token)
    user_id = int(payload.get("sub"))

    # Verifique se a sessão está ativa e não expirada
    sessao = db.query(Sessao).filter_by(token=token, utilizador_id=user_id, ativo=True).first()
    if not sessao or sessao.data_expiracao < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão expirada ou inválida."
        )

    utilizador = db.query(Utilizador).filter(Utilizador.id == user_id).first()
    if not utilizador or not utilizador.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Utilizador não encontrado ou inativo."
        )
    return utilizador