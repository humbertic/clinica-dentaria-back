"""Adding VW-Tables

Revision ID: 5d2710e41314
Revises: 335209d4dd64
Create Date: 2025-06-24 14:54:22.259001

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5d2710e41314'
down_revision: Union[str, None] = '335209d4dd64'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
CREATE_VIEWS = """
-- 1. Receita & Faturação
CREATE OR REPLACE VIEW vw_revenue_summary AS
SELECT
    date_trunc('day', f.data_emissao) AS dia,
    SUM(f.total)                      AS faturacao_total,
    SUM(fp.valor)                     AS receita_recebida,
    COUNT(DISTINCT f.id)              AS faturas_emitidas,
    COUNT(fp.id)                      AS pagamentos_realizados
FROM   "Faturas" f
LEFT   JOIN fatura_pagamentos fp ON fp.fatura_id = f.id
GROUP  BY dia;

-- 2. Top Serviços
CREATE OR REPLACE VIEW vw_top_services AS
SELECT
    fi.descricao      AS servico,
    SUM(fi.total)     AS valor_total
FROM   "FaturaItens" fi
GROUP  BY fi.descricao
ORDER  BY valor_total DESC;

-- 3. Caixa por sessão
CREATE OR REPLACE VIEW vw_cash_shift AS
SELECT
    cs.id                           AS session_id,
    cs.operador_id,
    cs.data_inicio,
    cs.data_fecho,
    cs.valor_inicial,
    COALESCE(SUM(cp.valor_pago),0)  AS total_entradas,
    cs.valor_final,
    (cs.valor_inicial + COALESCE(SUM(cp.valor_pago),0) - COALESCE(cs.valor_final,0))
                                    AS diferenca_teorica_real
FROM   "CaixaSessions" cs
LEFT   JOIN "CaixaPayments" cp ON cp.session_id = cs.id
GROUP  BY cs.id;

-- 4. Parcelas em atraso
CREATE OR REPLACE VIEW vw_overdue_installments AS
SELECT
    p.id                             AS parcela_id,
    p.fatura_id,
    p.numero,
    p.valor_planejado                AS valor_em_divida,
    p.data_vencimento,
    (CURRENT_DATE - p.data_vencimento::date) AS dias_em_atraso
FROM   "ParcelasPagamento" p
WHERE  p.estado <> 'paga'
  AND  p.data_vencimento IS NOT NULL
  AND  p.data_vencimento < CURRENT_DATE;

-- 5. Stock crítico
CREATE OR REPLACE VIEW vw_stock_critical AS
WITH saldo AS (
    SELECT
        i.id,
        SUM(
            CASE
                WHEN ms.tipo_movimento ILIKE ANY (ARRAY['entrada','ajuste_pos','devolucao'])
                     THEN  ms.quantidade
                ELSE - ms.quantidade
            END
        ) AS quantidade_atual
    FROM   "ItemStock" i
    LEFT   JOIN "MovimentoStock" ms ON ms.item_id = i.id
    GROUP  BY i.id
)
SELECT
    i.id,
    i.nome,
    s.quantidade_atual,
    i.quantidade_minima,
    MIN(il.validade) FILTER (WHERE il.quantidade > 0) AS validade_proxima
FROM       "ItemStock" i
JOIN       saldo s  ON s.id = i.id
LEFT JOIN  "ItemLote" il ON il.item_id = i.id
GROUP BY i.id, i.nome, s.quantidade_atual, i.quantidade_minima
HAVING s.quantidade_atual < i.quantidade_minima
   OR  MIN(il.validade) FILTER (WHERE il.quantidade > 0)
       <= CURRENT_DATE + INTERVAL '30 day';

-- 6. Produtividade clínica
CREATE OR REPLACE VIEW vw_productivity_clinical AS
SELECT
    date_trunc('month', c.data_inicio) AS mes,
    c.medico_id,
    COUNT(*) FILTER (WHERE c.estado = 'concluida') AS consultas_realizadas,
    AVG(EXTRACT(EPOCH FROM (c.data_fim - c.data_inicio)) / 60)::numeric(10,2)
                                          AS duracao_media_min
FROM   "Consultas" c
GROUP  BY mes, c.medico_id;
"""

DROP_VIEWS = """
DROP VIEW IF EXISTS vw_productivity_clinical;
DROP VIEW IF EXISTS vw_stock_critical;
DROP VIEW IF EXISTS vw_overdue_installments;
DROP VIEW IF EXISTS vw_cash_shift;
DROP VIEW IF EXISTS vw_top_services;
DROP VIEW IF EXISTS vw_revenue_summary;
"""

# ----------------------------------------------------------------------
def upgrade() -> None:
    op.execute(sa.text(CREATE_VIEWS))

def downgrade() -> None:
    op.execute(sa.text(DROP_VIEWS))
