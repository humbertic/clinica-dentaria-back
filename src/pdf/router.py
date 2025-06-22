from fastapi import APIRouter, Depends, HTTPException, status, Response, Query
from sqlalchemy.orm import Session
from src.database import SessionLocal
from src.utilizadores.dependencies import get_current_user
from src.pdf import service as pdf_service
from typing import Optional

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
    download: Optional[bool] = Query(False, description="Set to true to download instead of view"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Generate and return a PDF for an orçamento.
    Set download=true to download as file, or false (default) to view in browser.
    """
    try:
        pdf_bytes = pdf_service.generate_orcamento_pdf(orcamento_id, db)
        
        # Set appropriate headers based on download parameter
        headers = {}
        if download:
            # For download: use attachment disposition
            headers["Content-Disposition"] = f"attachment; filename=orcamento_{orcamento_id}.pdf"
        else:
            # For viewing: use inline disposition
            headers["Content-Disposition"] = f"inline; filename=orcamento_{orcamento_id}.pdf"
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers=headers
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating orçamento PDF: {str(e)}"
        )

@router.get("/fatura/{fatura_id}")
def get_fatura_pdf(
    fatura_id: int,
    download: Optional[bool] = Query(False, description="Set to true to download instead of view"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Generate and return a PDF invoice.
    Set download=true to download as file, or false (default) to view in browser.
    """
    try:
        pdf_bytes = pdf_service.generate_fatura_pdf(fatura_id, db)
        
        # Set appropriate headers based on download parameter
        headers = {}
        if download:
            # For download: use attachment disposition
            headers["Content-Disposition"] = f"attachment; filename=fatura_{fatura_id}.pdf"
        else:
            # For viewing: use inline disposition
            headers["Content-Disposition"] = f"inline; filename=fatura_{fatura_id}.pdf"
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers=headers
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating invoice PDF: {str(e)}"
        )