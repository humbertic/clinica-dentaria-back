from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.database import SessionLocal
from src.utilizadores.dependencies import get_current_user
from src.utilizadores.models import Utilizador
from src.utilizadores.utils import is_master_admin

from . import service, schemas

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post(
    "",
    response_model=schemas.CategoriaResponse,
    summary="Criar nova categoria (Master Admin)"
)
def criar_categoria(
    dados: schemas.CategoriaCreate,
    db: Session = Depends(get_db),
    usuario: Utilizador = Depends(get_current_user)
):
    if not is_master_admin(usuario):
        raise HTTPException(403, "Apenas Master Admin pode criar categorias.")
    return service.criar_categoria(db, dados, criado_por_id=usuario.id)

@router.get(
    "",
    response_model=list[schemas.CategoriaResponse],
    summary="Listar categorias"
)
def listar_categorias(
    db: Session = Depends(get_db),
    usuario: Utilizador = Depends(get_current_user)
):
    return service.listar_categorias(db)

@router.get(
    "/{categoria_id}",
    response_model=schemas.CategoriaResponse,
    summary="Obter categoria por ID"
)
def obter_categoria(
    categoria_id: int,
    db: Session = Depends(get_db),
    usuario: Utilizador = Depends(get_current_user)
):
    cat = service.obter_categoria_por_id(db, categoria_id)
    if not cat:
        raise HTTPException(404, "Categoria não encontrada.")
    return cat

@router.put(
    "/{categoria_id}",
    response_model=schemas.CategoriaResponse,
    summary="Atualizar categoria (Master Admin)"
)
def atualizar_categoria(
    categoria_id: int,
    dados: schemas.CategoriaUpdate,
    db: Session = Depends(get_db),
    usuario: Utilizador = Depends(get_current_user)
):
    if not is_master_admin(usuario):
        raise HTTPException(403, "Apenas Master Admin pode atualizar categorias.")
    cat = service.atualizar_categoria(db, categoria_id, dados, atualizado_por_id=usuario.id)
    if not cat:
        raise HTTPException(404, "Categoria não encontrada.")
    return cat

@router.delete(
    "/{categoria_id}",
    response_model=dict,
    summary="Remover categoria (Master Admin)"
)
def remover_categoria(
    categoria_id: int,
    db: Session = Depends(get_db),
    usuario: Utilizador = Depends(get_current_user)
):
    if not is_master_admin(usuario):
        raise HTTPException(403, "Apenas Master Admin pode remover categorias.")
    sucesso = service.remover_categoria(db, categoria_id, removido_por_id=usuario.id)
    if not sucesso:
        raise HTTPException(404, "Categoria não encontrada.")
    return {"detail": "Categoria removida com sucesso."}
