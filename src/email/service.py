"""
Fachada central para envio de e-mails:
  • Fatura  (PDF em anexo)
  • Orçamento (PDF em anexo)
  • Lembrete de consulta (sem anexo)
  • Cancelamento de consulta (sem anexo)
Usa a classe EmailService antiga     → importada como RawEmailService
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session
from jinja2 import Environment, FileSystemLoader

from src.email.raw_service import EmailService as RawEmailService
from src.email.schemas      import EmailAttachment, EmailConfig

# --------- serviços/DAO da tua app -----------------------------
from src.faturacao.service  import get_fatura
from src.orcamento.service  import get_orcamento
from src.pacientes.service  import obter_paciente
from src.clinica.service    import obter_clinica_por_id
from src.marcacoes.models   import Marcacao
from src.pdf.service        import generate_fatura_pdf, generate_orcamento_pdf

# ------------------ Jinja env partilhado -----------------------
TEMPLATE_DIR = Path(__file__).parent / "templates"
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
env.filters["dt"] = lambda dt: dt.strftime("%d/%m/%Y %H:%M")

# ------------------ Fachada principal --------------------------
class EmailManager:
    """
    Usa RawEmailService (FastMail) internamente.
    Recebe DB session para poder fazer look-ups e gerar PDFs.
    """

    def __init__(self, db: Session, cfg: EmailConfig):
        self.db   = db
        self.mail = RawEmailService(cfg)   # ← a tua classe antiga

    # ---------- Fatura -----------------------------------------
    async def enviar_fatura(
        self,
        fatura_id: int,
        clinica_id: int,
        email_para: Optional[str] = None
    ):
        fatura = get_fatura(self.db, fatura_id)
        if not fatura:
            raise HTTPException(404, "Fatura não encontrada")

        paciente = obter_paciente(self.db, fatura.paciente_id)
        clinica  = obter_clinica_por_id(self.db, clinica_id, None)

        destinatario = email_para or paciente.email
        if not destinatario:
            raise HTTPException(400, "Paciente sem e-mail e parâmetro email_para ausente")

        pdf  = generate_fatura_pdf(fatura_id, self.db)
        anexo = EmailAttachment(filename=f"fatura_{fatura_id}.pdf", content=pdf)

        await self.mail.enviar_email(
            assunto        = f"Fatura #{fatura_id}",
            destinatarios  = [destinatario],
            nome_template  = "fatura.html",
            dados_template = {
                "fatura": fatura,
                "paciente": paciente,
                "clinica": clinica,
            },
            anexos=[anexo],
        )

    # ---------- Orçamento --------------------------------------
    async def enviar_orcamento(
        self,
        orcamento_id: int,
        clinica_id: int,
        email_para: Optional[str] = None
    ):
        orcamento = get_orcamento(self.db, orcamento_id)
        if not orcamento:
            raise HTTPException(404, "Orçamento não encontrado")

        paciente = obter_paciente(self.db, orcamento.paciente_id)
        clinica  = obter_clinica_por_id(self.db, clinica_id, None)

        destinatario = email_para or paciente.email
        if not destinatario:
            raise HTTPException(400, "Paciente sem e-mail e parâmetro email_para ausente")

        pdf  = generate_orcamento_pdf(orcamento_id, self.db)
        anexo = EmailAttachment(filename=f"orcamento_{orcamento_id}.pdf", content=pdf)

        await self.mail.enviar_email(
            assunto        = f"Orçamento #{orcamento_id}",
            destinatarios  = [destinatario],
            nome_template  = "orcamento.html",
            dados_template = {
                "orcamento": orcamento,
                "paciente": paciente,
                "clinica": clinica,
            },
            anexos=[anexo],
        )

    # ---------- Lembrete (sem anexo) ----------------------------
    async def enviar_lembrete(self, marc: Marcacao):
        await self.mail.enviar_email(
            assunto        = f"Lembrete da sua consulta – {marc.data_hora_inicio:%d/%m %H:%M}",
            destinatarios  = [marc.paciente.email],
            nome_template  = "lembrete_consulta.html",
            dados_template = {
                "clinica":  marc.clinic,
                "paciente": marc.paciente,
                "medico":   marc.medico,
                "marcacao": marc,
            },
            anexos=[],
        )

    # ---------- Cancelamento (sem anexo) ------------------------
    async def enviar_cancelamento(self, marc: Marcacao):
        await self.mail.enviar_email(
            assunto        = f"Consulta cancelada – {marc.data_hora_inicio:%d/%m %H:%M}",
            destinatarios  = [marc.paciente.email],
            nome_template  = "consulta_cancelada.html",
            dados_template = {
                "clinica":  marc.clinic,
                "paciente": marc.paciente,
                "medico":   marc.medico,
                "marcacao": marc,
            },
            anexos=[],
        )
