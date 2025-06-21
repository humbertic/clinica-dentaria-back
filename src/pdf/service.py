"""
pdf_service.py  ·  Gerar PDFs (Fatura & Orçamento) com Jinja2 + WeasyPrint
"""

from __future__ import annotations

import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from fastapi import HTTPException, status
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML, CSS

from src.clinica.models import Clinica

# ──────────────────────────────────────────────────────────────
# Configuração global
# ──────────────────────────────────────────────────────────────

TEMPLATES_DIR = Path(__file__).parent / "templates"
ASSETS_DIR = TEMPLATES_DIR / "assets"
PDF_TMP_DIR = Path(__file__).parent / "generated_pdfs"
PDF_TMP_DIR.mkdir(exist_ok=True)

env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
    enable_async=False,          # alterar se quiser renderização async
)

# ─── filtro CVE ───────────────────────────────────────────────
def cve(value):
    """
    Formata para '1 234,56 CVE'.  Adapte se quiser 'Esc' ou 'CVE$'.
    Aceita float, int ou Decimal.
    """
    try:
        num = float(value)
    except (TypeError, ValueError):
        return value  # devolve como está se não for número

    formatted = f"{num:,.2f}".replace(",", " ").replace(".", ",")
    return f"{formatted} CVE"

env.filters["cve"] = cve

# ──────────────────────────────────────────────────────────────
# Utilitários genéricos
# ──────────────────────────────────────────────────────────────


def render_template(name: str, context: Dict[str, Any]) -> str:
    """Renderiza um ficheiro HTML através do Jinja2."""
    try:
        template = env.get_template(name)
        return template.render(**context)
    except Exception as exc:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao renderizar template '{name}': {exc}",
        ) from exc


def generate_pdf(
    html: str,
    css_files: Optional[List[str]] = None,
) -> bytes:
    """Transforma HTML em PDF, aplicando folhas de estilo opcionais."""
    try:
        # 1) gravar HTML num ficheiro temporário
        with tempfile.NamedTemporaryFile(
            suffix=".html", delete=False, dir=str(PDF_TMP_DIR)
        ) as tmp_html:
            tmp_html.write(html.encode("utf-8"))
            html_path = tmp_html.name

        # 2) preparar CSS
        styles: List[CSS] = []
        for css_name in (css_files or []):
            css_path = ASSETS_DIR / css_name
            if css_path.exists():
                styles.append(CSS(filename=str(css_path)))
            else:
                raise FileNotFoundError(f"CSS não encontrado: {css_path}")

        # 3) gerar PDF
        pdf_bytes = HTML(filename=html_path, base_url=str(TEMPLATES_DIR)).write_pdf(
            stylesheets=styles
        )

        # 4) limpar ficheiro temporário
        os.unlink(html_path)
        return pdf_bytes

    except Exception as exc:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao gerar PDF: {exc}",
        ) from exc


# ──────────────────────────────────────────────────────────────
# Funções específicas · Fatura
# ──────────────────────────────────────────────────────────────

def generate_fatura_pdf(fatura_id: int, db) -> bytes:
    """Gera PDF para a Fatura indicada."""
    from src.consultas.models import ConsultaItem
    from src.pacientes.models import PlanoItem
    from src.faturacao.service import get_fatura
    from src.clinica.service import get_clinica_details

    fatura = get_fatura(db, fatura_id)
    if not fatura:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail=f"Fatura ID={fatura_id} não encontrada.",
        )

    clinica = None
    if fatura.paciente:
        # Try to get clinic_id from patient if available
        paciente_id = fatura.paciente.id
        paciente_clinica_id = getattr(fatura.paciente, 'clinica_id', None)
        
        if paciente_clinica_id:
            clinica = db.query(Clinica).filter(Clinica.id == paciente_clinica_id).first()
            print(f"Found clinic {clinica.nome} from patient association")

    # If no clinic found via patient, try consulta or plano
    if not clinica and fatura.consulta_id and fatura.consulta:
        consulta_clinica_id = getattr(fatura.consulta, 'clinica_id', None)
        if consulta_clinica_id:
            clinica = db.query(Clinica).filter(Clinica.id == consulta_clinica_id).first()
            print(f"Found clinic {clinica.nome} from consulta association")
    
    if not clinica and fatura.plano_id and fatura.plano:
        plano_clinica_id = getattr(fatura.plano, 'clinica_id', None)
        if plano_clinica_id:
            clinica = db.query(Clinica).filter(Clinica.id == plano_clinica_id).first()
            print(f"Found clinic {clinica.nome} from plano association")

    # Fallback to default clinic if still not found
    if not clinica:
        clinica = get_clinica_details(db)
        print(f"Using default clinic: {clinica.nome}")

    # ── 1. Preparar itens ────────────────────────────────────
    itens = []
    for item in fatura.itens:
        numero_dente = None
        if item.origem_tipo == "consulta_item":
            ci = db.get(ConsultaItem, item.origem_id)
            numero_dente = getattr(ci, "numero_dente", None)
        elif item.origem_tipo == "plano_item":
            pi = db.get(PlanoItem, item.origem_id)
            numero_dente = getattr(pi, "numero_dente", None)

        itens.append(
            {
                "descricao": item.descricao or f"Item {item.id}",
                "origem_tipo": item.origem_tipo,
                "quantidade": item.quantidade,
                "preco_unitario": f"{float(item.preco_unitario):.2f}",
                "total": f"{float(item.total):.2f}",
                "numero_dente": numero_dente,
            }
        )

    # ── 2. Parcelas (se existirem) ───────────────────────────
    parcelas = []
    for p in (fatura.parcelas or []):
        parcelas.append(
            {
                "numero": p.numero,
                "valor_planejado": f"{float(p.valor_planejado):.2f}",
                "data_vencimento": p.data_vencimento.strftime("%d/%m/%Y")
                if p.data_vencimento
                else "—",
                "valor_pago": f"{float(p.valor_pago):.2f}" if p.valor_pago else None,
                "data_pagamento": p.data_pagamento.strftime("%d/%m/%Y")
                if p.data_pagamento
                else None,
                "estado": getattr(p.estado, "value", p.estado),
                "metodo_pagamento": p.metodo_pagamento,
            }
        )

    # ── 3. Consulta / Plano (opcionais) ───────────────────────
    consulta_ctx = (
        {
            "id": fatura.consulta.id,
            "data_inicio": fatura.consulta.data_inicio.strftime("%d/%m/%Y"),
        }
        if fatura.consulta_id and fatura.consulta
        else None
    )
    plano_ctx = (
        {
            "id": fatura.plano.id,
            "descricao": getattr(fatura.plano, "descricao", f"Plano {fatura.plano.id}"),
        }
        if fatura.plano_id and fatura.plano
        else None
    )

    # ── 4. Contexto Jinja2 ───────────────────────────────────
    context: Dict[str, Any] = {
        "clinica": clinica,
        "fatura": {
            "id": fatura.id,
            "data_emissao": fatura.data_emissao.strftime("%d/%m/%Y")
            if fatura.data_emissao
            else "N/A",
            "tipo": getattr(fatura.tipo, "value", fatura.tipo),
            "estado": getattr(fatura.estado, "value", fatura.estado),
            "total": f"{float(fatura.total):.2f}",
            "itens": itens,
            "parcelas": parcelas,
        },
        "paciente": {
            "nome": fatura.paciente.nome,
            "morada": fatura.paciente.morada or "—",
            "telefone": fatura.paciente.telefone or "—",
            "email": fatura.paciente.email or "—",
            "nif": getattr(fatura.paciente, "nif", "—"),
        },
        "consulta": consulta_ctx,
        "plano": plano_ctx,
        "data_geracao": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "logo_path": str(ASSETS_DIR / "logo.png")
        if (ASSETS_DIR / "logo.png").exists()
        else None,
    }

    # ── 5. Renderizar & gerar PDF ────────────────────────────
    html = render_template("fatura.html", context)
    return generate_pdf(html, css_files=["styles.css"])


# ──────────────────────────────────────────────────────────────
# Funções específicas · Orçamento
# ──────────────────────────────────────────────────────────────

def generate_orcamento_pdf(orcamento_id: int, db) -> bytes:
    """Gera PDF para Orçamento."""
    from src.orcamento.service import get_orcamento
    from src.clinica.service import get_clinica_details

    orcamento = get_orcamento(db, orcamento_id)
    if not orcamento:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail=f"Orçamento ID={orcamento_id} não encontrado.",
        )

    clinica = None
    if orcamento.paciente:
        # Try to get clinic_id from patient
        paciente_clinica_id = getattr(orcamento.paciente, 'clinica_id', None)
        
        if paciente_clinica_id:
            clinica = db.query(Clinica).filter(Clinica.id == paciente_clinica_id).first()
            print(f"Found clinic {clinica.nome} from patient association")

    # Fallback to direct orçamento association
    if not clinica:
        orcamento_clinica_id = getattr(orcamento, 'clinica_id', None)
        if orcamento_clinica_id:
            clinica = db.query(Clinica).filter(Clinica.id == orcamento_clinica_id).first()
            print(f"Found clinic {clinica.nome} from orcamento association")

    # Fallback to default clinic if still not found
    if not clinica:
        clinica = get_clinica_details(db)
        print(f"Using default clinic: {clinica.nome}")

    # Totais separados
    total_tratamentos = 0.0
    total_proteses = 0.0
    for it in orcamento.itens:
        categoria = getattr(it.artigo, "categoria", "")
        if categoria == "protese":
            total_proteses += float(it.subtotal_paciente)
        else:
            total_tratamentos += float(it.subtotal_paciente)

    context: Dict[str, Any] = {
        "clinica": clinica,
        "orcamento": {
            "id": orcamento.id,
            "data": orcamento.data.strftime("%d/%m/%Y") if orcamento.data else "—",
            "estado": getattr(orcamento.estado, "value", "—"),
            "observacoes": getattr(orcamento, "observacoes", ""),
            "itens": [
                {
                    "artigo": {
                        "codigo": it.artigo.codigo,
                        "nome": it.artigo.descricao,
                    },
                    "numero_dente": getattr(it, "numero_dente", ""),
                    "face": getattr(it, "face", ""),
                    "preco_paciente": float(it.preco_paciente),
                    "subtotal_paciente": float(it.subtotal_paciente),
                    "subtotal_entidade": float(
                        getattr(it, "subtotal_entidade", 0.0)
                    ),
                }
                for it in orcamento.itens
            ],
            "total_paciente": float(getattr(orcamento, "total_paciente", 0)),
            "total_entidade": float(getattr(orcamento, "total_entidade", 0)),
        },
        "paciente": {
            "nome": orcamento.paciente.nome,
            "numero_documento": getattr(orcamento.paciente, "numero_documento", "—"),
        },
        "entidade": {
            "nome": getattr(orcamento.entidade, "nome", "PARTICULAR")
            if getattr(orcamento, "entidade", None)
            else "PARTICULAR"
        },
        "total_tratamentos": total_tratamentos,
        "total_proteses": total_proteses,
        "data_geracao": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "logo_path": str(ASSETS_DIR / "logo.png")
        if (ASSETS_DIR / "logo.png").exists()
        else None,
    }
    print(f"Contexto para orçamento {orcamento_id}: {context}")
    html = render_template("orcamento.html", context)
    return generate_pdf(html, css_files=["styles.css"])
