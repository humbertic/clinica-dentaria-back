from sqlalchemy.orm import Session
from src.auditoria import models as auditoria_models
from src.utilizadores.models import Utilizador

def listar_auditoria(db: Session):
    auditorias = db.query(auditoria_models.Auditoria).all()
    respostas = []
    for a in auditorias:
        utilizador_nome = a.utilizador.nome if a.utilizador else None
        objeto_nome = None
        if a.objeto == "Utilizador" and a.objeto_id:
            u = db.query(Utilizador).filter_by(id=a.objeto_id).first()
            objeto_nome = u.nome if u else None
        # Adapte para outros objetos se necessário
        respostas.append({
            "id": a.id,
            "utilizador_id": a.utilizador_id,
            "utilizador_nome": utilizador_nome,
            "acao": a.acao,
            "objeto": a.objeto,
            "objeto_id": a.objeto_id,
            "objeto_nome": objeto_nome,
            "detalhes": a.detalhes,
            "data": a.data,
        })
    return respostas