from passlib.context import CryptContext
from src.utilizadores import models

# Contexto para hashing seguro de palavras-passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Gera o hash seguro da palavra-passe."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a palavra-passe corresponde ao hash armazenado."""
    return pwd_context.verify(plain_password, hashed_password)


def is_master_admin(utilizador: models.Utilizador) -> bool:
    for utilizador_clinica in utilizador.perfis:
        # You need to load the related Perfil object
        perfil = getattr(utilizador_clinica, "perfil", None)
        if perfil and perfil.nome == "Master Admin":
            return True
    return False

def is_frontdesk(utilizador: models.Utilizador) -> bool:
    for utilizador_clinica in utilizador.perfis:
        # You need to load the related Perfil object
        perfil = getattr(utilizador_clinica, "perfil", None)
        if perfil and perfil.nome == "Funcionário de Atendimento":
            return True
    return False