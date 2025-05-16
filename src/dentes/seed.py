from src.database import SessionLocal
from src.dentes.models import Dente, Face

FDI_PERM = [f"{q}{p}" for q in range(1, 5) for p in range(1, 9)]   # 11-48
FDI_DEC  = [f"{q}{p}" for q in range(5, 9) for p in range(1, 6)]   # 51-85

def run():
    db = SessionLocal()

    # Dentes
    if not db.query(Dente).first():
        for code in FDI_PERM + FDI_DEC:
            db.add(
                Dente(
                    id=int(code),
                    codigo_fdi=code,
                    tipo="permanente" if int(code) < 50 else "deciduo",
                    arcada="superior" if code[0] in ("1", "2", "5", "6") else "inferior",
                    quadrante=int(code[0]),
                    posicao=int(code[1]),
                )
            )

    # Faces
    faces = [
        ("M", "Mesial"),
        ("D", "Distal"),
        ("V", "Vestibular"),
        ("L", "Lingual"),
        ("O", "Oclusal"),
        ("I", "Incisal"),
    ]
    for fid, desc in faces:
        if not db.get(Face, fid):
            db.add(Face(id=fid, descricao=desc))

    db.commit()
    db.close()
