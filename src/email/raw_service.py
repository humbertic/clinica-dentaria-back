import os
import tempfile
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import HTTPException
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from tenacity import retry, stop_after_attempt, wait_exponential
from jinja2 import Environment, FileSystemLoader

from src.email.schemas import EmailAttachment, EmailConfig   # mantém como estava

logger = logging.getLogger("app.email")


class EmailService:
    """Serviço de baixo nível que envia e-mails usando FastMail."""

    def __init__(self, config: EmailConfig):
        self.config = config

        self.connection_config = ConnectionConfig(
            MAIL_USERNAME   = config.utilizador_smtp,
            MAIL_PASSWORD   = config.password_smtp,
            MAIL_FROM       = (
                f"{config.nome_remetente} <{config.remetente}>"
                if config.nome_remetente else config.remetente
            ),
            MAIL_PORT       = config.smtp_porta,
            MAIL_SERVER     = config.smtp_host,
            MAIL_STARTTLS   = config.usar_tls,
            MAIL_SSL_TLS    = config.usar_ssl,
            USE_CREDENTIALS = True,
            VALIDATE_CERTS  = True,
            TEMPLATE_FOLDER = Path(__file__).parent / "templates",
        )

        self.fast_mail = FastMail(self.connection_config)

    # ------------------------------------------------------------------
    #  Enviar e-mail (com ou sem template / anexos) — 3 tentativas
    # ------------------------------------------------------------------
    @retry(stop=stop_after_attempt(3),
           wait=wait_exponential(multiplier=1, min=4, max=10))
    async def enviar_email(
        self,
        assunto: str,
        destinatarios: List[str],
        corpo: Optional[str] = None,          # texto simples
        html_corpo: Optional[str] = None,     # html pré-gerado
        nome_template: Optional[str] = None,  # ficheiro Jinja
        dados_template: Optional[Dict[str, Any]] = None,
        anexos: Optional[List[EmailAttachment]] = None,
    ) -> bool:
        """
        Envia um e-mail:
          • Usa `nome_template`+`dados_template` → renderiza HTML.
          • Ou `html_corpo` / `corpo` se fornecidos.
          • Suporta anexos (EmailAttachment.content em bytes).
        Lança HTTPException 500 se falhar após 3 tentativas.
        """
        try:
            subtype = "html" if (html_corpo or nome_template) else "plain"

            # ------------------ anexos → ficheiros temporários -----------
            temp_files: List[str] = []
            attach_paths: List[str] = []

            if anexos:
                for a in anexos:
                    tmp = tempfile.NamedTemporaryFile(
                        delete=False, suffix=f"_{a.filename}"
                    )
                    tmp.write(a.content)
                    tmp.flush()
                    temp_files.append(tmp.name)
                    attach_paths.append(tmp.name)

            try:
                # -------- renderização do corpo -------------------------
                body_content = corpo or html_corpo or ""
                if nome_template:
                    env = Environment(
                        loader=FileSystemLoader(
                            Path(__file__).parent / "templates"
                        )
                    )
                    env.filters["dt"] = lambda dt: dt.strftime("%d/%m/%Y %H:%M")
                    tmpl = env.get_template(nome_template)
                    body_content = tmpl.render(**(dados_template or {}))

                # -------- construir mensagem & enviar -------------------
                msg = MessageSchema(
                    subject     = assunto,
                    recipients  = destinatarios,
                    body        = body_content,
                    subtype     = subtype,
                    attachments = attach_paths,
                )
                await self.fast_mail.send_message(msg)
                logger.info(
                    "Email enviado para %s – %s",
                    ", ".join(destinatarios), assunto
                )
                return True

            finally:
                # apagar temp files
                for path in temp_files:
                    try:
                        os.unlink(path)
                    except Exception as exc:
                        logger.warning("Falha ao apagar %s: %s", path, exc)

        except Exception as exc:
            logger.error("Falha ao enviar email: %s", exc)
            raise HTTPException(
                status_code=500,
                detail=f"Falha ao enviar email: {exc}"
            ) from exc
