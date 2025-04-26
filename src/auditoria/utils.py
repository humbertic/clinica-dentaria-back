from src.auditoria import models as auditoria_models

def registrar_auditoria(db, utilizador_id: int, acao: str, objeto: str, objeto_id: int = None, detalhes: str = None):
    registro = auditoria_models.Auditoria(
        utilizador_id=utilizador_id,
        acao=acao,
        objeto=objeto,
        objeto_id=objeto_id,
        detalhes=detalhes
    )
    db.add(registro)
    db.commit()