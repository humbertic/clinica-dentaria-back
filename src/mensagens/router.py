# src/mensagens/router.py
from fastapi import APIRouter, Depends, WebSocket, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from src.database import SessionLocal
from src.utilizadores.dependencies import get_current_user
from src.utilizadores.models import Utilizador, Sessao, UtilizadorClinica
from src.utilizadores.jwt import verify_token  # Import your existing verify_token function

from . import schemas, service, ws

router = APIRouter(prefix="/mensagens", tags=["Mensagens"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------- REST ----------
@router.post("", response_model=schemas.MessageRead)
async def enviar_mensagem(
    dados: schemas.MessageCreate,
    db: Session = Depends(get_db),
    user: Utilizador = Depends(get_current_user),
):
    msg = service.criar_mensagem(db, user, dados)
    await ws.manager.broadcast(f"clinica-{msg.clinica_id}", {
        "id": msg.id,
        "texto": msg.texto,
        "remetente_id": msg.remetente_id,
        "remetente_nome": user.nome, 
        "clinica_id": msg.clinica_id,
        "thread_id": msg.thread_id,
        "created_at": msg.created_at.isoformat(),
    })
    return msg


@router.get("/clinic-thread", response_model=schemas.ThreadRead)
def get_clinic_thread(
    clinica_id: int = Query(...),
    db: Session = Depends(get_db),
    user: Utilizador = Depends(get_current_user),
):
    """Get or create a clinic-wide thread for all users in a clinic."""
    # Verify user belongs to the clinic
    is_member = db.query(UtilizadorClinica).filter_by(
        utilizador_id=user.id,
        clinica_id=clinica_id
    ).first() is not None
    
    if not is_member:
        raise HTTPException(
            status_code=403,
            detail="Usuário não pertence a esta clínica."
        )
    
    # Get or create the clinic thread
    thread = service._get_or_create_clinic_thread(db, clinica_id)
    
    # Format the response
    return {
        "id": thread.id,
        "clinica_id": clinica_id,
        "tipo": "clinic",
        "nome": thread.nome or "Clínica Geral"
    }


@router.get("/threads", response_model=List[schemas.ThreadRead])
def minhas_threads(
    clinica_id: int = Query(...),
    db: Session = Depends(get_db),
    user: Utilizador = Depends(get_current_user),
):
    return service.listar_threads(db, user.id, clinica_id)


@router.get("/thread/{thread_id}", response_model=List[schemas.MessageRead])
def historico(
    thread_id: int,
    clinica_id: int = Query(...),
    before_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user: Utilizador = Depends(get_current_user),
    limit: int = 30
):
    return service.listar_mensagens(db, thread_id, clinica_id, limit, before_id)

# ---------- WebSocket ----------
@router.websocket("/ws/clinica/{clinica_id}")
async def ws_clinica(
    websocket: WebSocket,
    clinica_id: int,
    token: str = Query(..., alias="token")  # token via query
):
    try:
        # Use your existing verification system
        db = next(get_db())
        
        # Verify token and get user ID
        payload = verify_token(token)
        user_id = int(payload.get("sub"))
        
        # Verify session is active
        sessao = db.query(Sessao).filter_by(
            token=token, 
            utilizador_id=user_id, 
            ativo=True
        ).first()
        
        if not sessao or sessao.data_expiracao < datetime.utcnow():
            await websocket.close(code=4001, reason="Sessão expirada ou inválida")
            return
            
        # Get user
        utilizador = db.query(Utilizador).filter(
            Utilizador.id == user_id,
            Utilizador.ativo == True
        ).first()
        
        if not utilizador:
            await websocket.close(code=4003, reason="Utilizador não encontrado ou inativo")
            return
            
        # Verify user belongs to this clinic
        # This depends on your data model - adjust as needed
        is_member = db.query(UtilizadorClinica).filter_by(
            utilizador_id=user_id,
            clinica_id=clinica_id
        ).first() is not None
        
        if not is_member:
            await websocket.close(code=4003, reason="Usuário não pertence a esta clínica")
            return
        
    except Exception as e:
        print(f"WebSocket authentication error: {e}")
        await websocket.close(code=4003, reason="Falha na autenticação")
        return
    finally:
        db.close()

    # If we get here, authentication was successful
    await ws.clinic_chat_ws(websocket, clinica_id, user_id)