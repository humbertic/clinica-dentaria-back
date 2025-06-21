from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from src.database import SessionLocal
from src.utilizadores.dependencies import get_current_user
from src.pdf import service as pdf_service

router = APIRouter(
    prefix="/pdf",
    tags=["PDF"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/orcamento/{orcamento_id}")
def get_orcamento_pdf(
    orcamento_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Generate and return a PDF for an orçamento.
    """
    try:
        pdf_bytes = pdf_service.generate_orcamento_pdf(orcamento_id, db)
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=orcamento_{orcamento_id}.pdf"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating orçamento PDF: {str(e)}"
        )

@router.get("/fatura/{fatura_id}")
def get_fatura_pdf(
    fatura_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Generate and return a PDF invoice.
    """
    try:
        pdf_bytes = pdf_service.generate_fatura_pdf(fatura_id, db)
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=fatura_{fatura_id}.pdf"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating invoice PDF: {str(e)}"
        )