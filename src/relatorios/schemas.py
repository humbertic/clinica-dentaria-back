from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict
from typing import Optional

# ---------- Receita & Faturação ----------
class RevenueSummaryOut(BaseModel):
    dia: datetime
    faturacao_total: Decimal
    receita_recebida: Decimal
    faturas_emitidas: int
    pagamentos_realizados: int

    model_config = ConfigDict(from_attributes=True)

# ---------- Top Serviços ----------
class TopServiceOut(BaseModel):
    servico: str
    valor_total: Decimal

# ---------- Caixa ----------
class CashShiftOut(BaseModel):
    session_id: int
    operador_id: int
    data_inicio: datetime
    data_fecho: Optional[datetime]
    valor_inicial: Decimal
    total_entradas: Decimal
    valor_final: Optional[Decimal]
    diferenca_teorica_real: Decimal

    model_config = ConfigDict(from_attributes=True)

# ---------- Parcelas em atraso ----------
class OverdueInstallmentOut(BaseModel):
    parcela_id: int
    fatura_id: int
    numero: int
    valor_em_divida: Decimal
    data_vencimento: datetime
    dias_em_atraso: int

    model_config = ConfigDict(from_attributes=True)

# ---------- Stock crítico ----------
class StockCriticalOut(BaseModel):
    id: int
    nome: str
    quantidade_atual: Optional[int] 
    quantidade_minima: int
    validade_proxima: Optional[date]

    model_config = ConfigDict(from_attributes=True)

# ---------- Produtividade ----------
class ProductivityClinicalOut(BaseModel):
    mes: datetime
    medico_id: Optional[int]
    consultas_realizadas: int
    duracao_media_min: Optional[Decimal]

    model_config = ConfigDict(from_attributes=True)
