from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status
from src.utilizadores import models, schemas, utils
from src.utilizadores.utils import is_master_admin
from src.auditoria.utils import registrar_auditoria
from datetime import datetime, timedelta

def criar_utilizador(
    db: Session, 
    dados: schemas.UtilizadorCreate, 
    is_master_admin: bool = False
) -> models.Utilizador:
    # Verificar unicidade de username, email e telefone
    if db.query(models.Utilizador).filter(models.Utilizador.username == dados.username).first():
        raise HTTPException(status_code=400, detail="Username já está registado.")
    if db.query(models.Utilizador).filter(models.Utilizador.email == dados.email).first():
        raise HTTPException(status_code=400, detail="Email já está registado.")
    if db.query(models.Utilizador).filter(models.Utilizador.telefone == dados.telefone).first():
        raise HTTPException(status_code=400, detail="Telefone já está registado.")

    # Criar objeto Utilizador com password encriptada
    novo_utilizador = models.Utilizador(
        username=dados.username,
        nome=dados.nome,
        email=dados.email,
        telefone=dados.telefone,
        password_hash=utils.hash_password(dados.password)
    )
    db.add(novo_utilizador)
    db.commit()
    db.refresh(novo_utilizador)

    # Atribuir perfil Master Admin se necessário
    if is_master_admin:
        perfil_master = db.query(models.Perfil).filter(models.Perfil.nome == "Master Admin").first()
        if not perfil_master:
            perfil_master = models.Perfil(nome="Master Admin")
            db.add(perfil_master)
            db.commit()
            db.refresh(perfil_master)
        utilizador_clinica = models.UtilizadorClinica(
            utilizador_id=novo_utilizador.id,
            perfil_id=perfil_master.id,
            ativo=True
        )
        db.add(utilizador_clinica)
        db.commit()
        registrar_auditoria(
        db,
        novo_utilizador.id,  # ou admin_id se for admin criando
        "Criação",
        "Utilizador",
        novo_utilizador.id,
        f"Utilizador {novo_utilizador.username} criado."
        )

    return novo_utilizador

def autenticar_utilizador(db: Session, email_or_username: str, password: str) -> models.Utilizador:
    utilizador = db.query(models.Utilizador).filter(
        (models.Utilizador.email == email_or_username) | (models.Utilizador.username == email_or_username)
    ).first()
    if not utilizador:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas.")

    if utilizador.bloqueado:
        raise HTTPException(status_code=403, detail="Conta bloqueada por excesso de tentativas. Contacte o Master Admin.")

    if not utils.verify_password(password, utilizador.password_hash):
        utilizador.tentativas_falhadas += 1
        if utilizador.tentativas_falhadas >= 5:
            utilizador.bloqueado = True
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas.")

    if not utilizador.ativo:
        raise HTTPException(status_code=403, detail="Conta desativada.")

    # Reset tentativas ao fazer login com sucesso
    utilizador.tentativas_falhadas = 0
    db.commit()
    
    

    return utilizador

def atribuir_clinicas(db: Session, utilizador_id: int, clinica_ids: list[int]):
    # Verifica se o utilizador tem perfil global
    global_assoc = db.query(models.UtilizadorClinica).filter_by(
        utilizador_id=utilizador_id,
        clinica_id=None,
        ativo=True
    ).first()
    if not global_assoc:
        raise HTTPException(status_code=400, detail="Utilizador não tem perfil global atribuído.")

    perfil_id = global_assoc.perfil_id

    # Remove associações antigas (opcional, se quiser sobrescrever)
    db.query(models.UtilizadorClinica).filter(
        models.UtilizadorClinica.utilizador_id == utilizador_id,
        models.UtilizadorClinica.clinica_id != None
    ).delete(synchronize_session=False)

    # Associa cada clínica nova
    for clinica_id in clinica_ids:
        assoc = db.query(models.UtilizadorClinica).filter_by(
            utilizador_id=utilizador_id,
            clinica_id=clinica_id
        ).first()
        if assoc:
            assoc.ativo = True
            assoc.perfil_id = perfil_id
        else:
            assoc = models.UtilizadorClinica(
                utilizador_id=utilizador_id,
                clinica_id=clinica_id,
                perfil_id=perfil_id,
                ativo=True
            )
            db.add(assoc)
    db.commit()

def listar_utilizadores(db: Session):
    utilizadores = db.query(models.Utilizador).all()
    result = []
    for utilizador in utilizadores:
        perfil_dict = None
        clinicas_list = []
        if utilizador.perfis:
            for uc in utilizador.perfis:
                if uc.ativo and uc.perfil:
                    # Global perfil (clinica_id is None)
                    if uc.clinica_id is None and not perfil_dict:
                        perfil_dict = {
                            "id": uc.perfil.id,
                            "perfil": uc.perfil.perfil,
                            "nome": uc.perfil.nome
                        }
                    # Clinic association
                    if uc.clinica_id is not None and uc.clinica:
                        clinicas_list.append({
                            "clinica": {
                                "id": uc.clinica.id,
                                "nome": uc.clinica.nome
                            },
                            "perfil": {
                                "id": uc.perfil.id,
                                "perfil": uc.perfil.perfil,
                                "nome": uc.perfil.nome
                            }
                        })
        result.append({
            "id": utilizador.id,
            "username": utilizador.username,
            "nome": utilizador.nome,
            "email": utilizador.email,
            "telefone": utilizador.telefone,
            "ativo": utilizador.ativo,
            "bloqueado": utilizador.bloqueado,
            "perfil": perfil_dict,
            "clinicas": clinicas_list
        })
    return result



def obter_utilizador(db: Session, user_id: int):
    utilizador = db.query(models.Utilizador).filter_by(id=user_id).first()
    if not utilizador:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado")
    perfil_dict = None
    clinicas_list = []
    if utilizador.perfis:
        for uc in utilizador.perfis:
            if uc.ativo and uc.perfil:
                # Global perfil (clinica_id is None)
                if uc.clinica_id is None and not perfil_dict:
                    perfil_dict = {
                        "id": uc.perfil.id,
                        "perfil": uc.perfil.perfil,
                        "nome": uc.perfil.nome
                    }
                # Clinic association
                if uc.clinica_id is not None and uc.clinica:
                    clinicas_list.append({
                        "clinica": {
                            "id": uc.clinica.id,
                            "nome": uc.clinica.nome
                        }
                        
                    })
    return {
        "id": utilizador.id,
        "username": utilizador.username,
        "nome": utilizador.nome,
        "email": utilizador.email,
        "telefone": utilizador.telefone,
        "ativo": utilizador.ativo,
        "bloqueado": utilizador.bloqueado,
        "perfil": perfil_dict,
        "clinicas": clinicas_list
    }

def atualizar_utilizador(db: Session, user_id: int, dados: schemas.UtilizadorUpdate) -> models.Utilizador:
    utilizador = db.query(models.Utilizador).filter_by(id=user_id).first()
    if not utilizador:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado")
    utilizador.nome = dados.nome
    utilizador.telefone = dados.telefone
    db.commit()
    db.refresh(utilizador)
    registrar_auditoria(
        db,
        user_id,
        "Atualização",
        "Utilizador",
        user_id,
        f"Dados pessoais atualizados."
    )
    return utilizador

def admin_atualizar_utilizador(db: Session, user_id: int, dados: schemas.UtilizadorAdminUpdate, admin_id: int) -> models.Utilizador:
    utilizador = db.query(models.Utilizador).filter_by(id=user_id).first()
    if not utilizador:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado")
    utilizador.nome = dados.nome
    utilizador.telefone = dados.telefone
    if dados.ativo is not None:
        utilizador.ativo = dados.ativo
    db.commit()
    db.refresh(utilizador)
    registrar_auditoria(
        db,
        admin_id,
        "Atualização (admin)",
        "Utilizador",
        user_id,
        f"Dados do utilizador {user_id} atualizados pelo admin."
    )
    return utilizador


def suspender_utilizador(db: Session, user_id: int, admin_id: int) -> models.Utilizador:
    utilizador = db.query(models.Utilizador).filter_by(id=user_id).first()
    if not utilizador:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado")
    utilizador.ativo = False
    db.commit()
    db.refresh(utilizador)
    registrar_auditoria(
        db, admin_id, "Suspensão", "Utilizador", user_id,
        f"Conta do utilizador {user_id} suspensa."
    )
    return utilizador

def ativar_utilizador(db: Session, user_id: int, admin_id: int) -> models.Utilizador:
    utilizador = db.query(models.Utilizador).filter_by(id=user_id).first()
    if not utilizador:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado")
    utilizador.ativo = True
    db.commit()
    db.refresh(utilizador)
    registrar_auditoria(
        db, admin_id, "Ativação", "Utilizador", user_id,
        f"Conta do utilizador {user_id} ativada."
    )
    return utilizador

def desbloquear_utilizador(db: Session, user_id: int, admin_id: int) -> models.Utilizador:
    utilizador = db.query(models.Utilizador).filter_by(id=user_id).first()
    if not utilizador:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado")
    utilizador.bloqueado = False
    utilizador.tentativas_falhadas = 0
    db.commit()
    db.refresh(utilizador)
    registrar_auditoria(
        db, admin_id, "Desbloqueio", "Utilizador", user_id,
        f"Conta do utilizador {user_id} desbloqueada."
    )
    return utilizador

def atribuir_perfil(db: Session, user_id: int, perfil_id: int, admin_id: int):
    # Only update or create the global perfil (clinica_id=None)
    global_relacao = db.query(models.UtilizadorClinica).filter_by(
        utilizador_id=user_id,
        clinica_id=None
    ).first()
    if global_relacao:
        global_relacao.perfil_id = perfil_id
        global_relacao.ativo = True
        db.commit()
        db.refresh(global_relacao)
        relacao = global_relacao
    else:
        relacao = models.UtilizadorClinica(
            utilizador_id=user_id,
            perfil_id=perfil_id,
            clinica_id=None,
            ativo=True
        )
        db.add(relacao)
        db.commit()
        db.refresh(relacao)
    registrar_auditoria(
        db, admin_id, "Atribuição de perfil global", "Utilizador", user_id,
        f"Perfil global {perfil_id} atribuído ao utilizador {user_id}."
    )
    return relacao

def remover_perfil(db: Session, user_id: int, perfil_id: int, admin_id: int):
    relacao = db.query(models.UtilizadorClinica).filter_by(utilizador_id=user_id, perfil_id=perfil_id).first()
    if not relacao:
        raise HTTPException(status_code=404, detail="Perfil não atribuído ao utilizador.")
    db.delete(relacao)
    db.commit()
    registrar_auditoria(
        db, admin_id, "Remoção de perfil", "Utilizador", user_id,
        f"Perfil {perfil_id} removido do utilizador {user_id}."
    )
    return {"detail": "Perfil removido com sucesso."}

def criar_sessao(db: Session, utilizador_id: int, token: str, expira_em: datetime):
    sessao = models.Sessao(
        utilizador_id=utilizador_id,
        token=token,
        data_expiracao=expira_em,
        ativo=True
    )
    db.add(sessao)
    db.commit()
    db.refresh(sessao)
    registrar_auditoria(
        db,
        utilizador_id,
        "Login",
        "Sessao",
        sessao.id,
        "Login efetuado com sucesso."
    )
    return sessao

def logout(db: Session, utilizador_id: int, token: str):
    sessao = db.query(models.Sessao).filter_by(token=token, utilizador_id=utilizador_id, ativo=True).first()
    if not sessao:
        raise HTTPException(status_code=404, detail="Sessão não encontrada ou já encerrada.")
    sessao.ativo = False
    db.commit()
    from src.auditoria.utils import registrar_auditoria
    registrar_auditoria(
        db,
        utilizador_id,
        "Logout",
        "Sessao",
        sessao.id,
        "Logout efetuado com sucesso."
    )
    return {"detail": "Logout efetuado com sucesso."}

def alterar_senha(db: Session, user_id: int, senha_atual: str, nova_senha: str):
    utilizador = db.query(models.Utilizador).filter_by(id=user_id).first()
    if not utilizador:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado")
    if not utils.verify_password(senha_atual, utilizador.password_hash):
        raise HTTPException(status_code=400, detail="Senha atual incorreta.")
    utilizador.password_hash = utils.hash_password(nova_senha)
    db.commit()
    registrar_auditoria(
        db,
        user_id,
        "Alteração de senha",
        "Utilizador",
        user_id,
        "Senha alterada pelo próprio utilizador."
    )
    return {"detail": "Senha alterada com sucesso."}


def obter_me(db: Session, utilizador_id: int):
    utilizador = db.query(models.Utilizador).filter_by(id=utilizador_id).first()
    perfil_dict = None
    clinicas_list = []
    if utilizador and utilizador.perfis:
        for uc in utilizador.perfis:
            if uc.ativo and uc.perfil:
                # Global perfil (clinica_id is None)
                if uc.clinica_id is None and not perfil_dict:
                    perfil_dict = {
                        "id": uc.perfil.id,              
                        "perfil": uc.perfil.perfil,
                        "nome": uc.perfil.nome
                    }
                # Clinic association
                if uc.clinica_id is not None and uc.clinica:
                    clinicas_list.append({
                        "clinica": {
                            "id": uc.clinica.id,
                            "nome": uc.clinica.nome
                        }
                        
                    })
    return {
        "id": utilizador.id,
        "username": utilizador.username,
        "nome": utilizador.nome,
        "email": utilizador.email,
        "telefone": utilizador.telefone,
        "ativo": utilizador.ativo,
        "bloqueado": utilizador.bloqueado,
        "perfil": perfil_dict,
        "clinicas": clinicas_list
    }
    
    

def listar_medicos_por_clinica(db: Session, clinica_id: int) -> list[models.Utilizador]:
    """
    Retorna todos os utilizadores cujo perfil em UtilizadorClinica
    é 'doctor' e que estejam ativos na clínica dada.
    """
    return (
        db.query(models.Utilizador)
          .join(models.UtilizadorClinica, models.Utilizador.perfis)
          .join(models.Perfil)
          .filter(
              models.UtilizadorClinica.clinica_id == clinica_id,
              models.UtilizadorClinica.ativo == True,
              func.lower(models.Perfil.perfil) == "doctor"
          )
          .all()
    )
    
    
