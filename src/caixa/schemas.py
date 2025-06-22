from datetime import datetime
from enum import Enum
from typing import Dict, Optional, List
from pydantic import BaseModel, Field

class CaixaStatus(str, Enum):
    aberto = "aberto"
    fechado = "fechado"

class PaymentMethodTotal(BaseModel):
    count: int
    total: float

class PaymentSummary(BaseModel):
    count: int
    total: float
    by_method: Dict[str, PaymentMethodTotal]


class CaixaSessionBase(BaseModel):
    operador_id:   Optional[int] = None 
    valor_inicial: float   = Field(..., description="Valor inicial em caixa")

class CaixaSessionCreate(CaixaSessionBase):
    pass

class CaixaSessionRead(CaixaSessionBase):
    id:            int
    data_inicio:   datetime
    status:        CaixaStatus
    valor_final:   Optional[float]
    data_fecho:    Optional[datetime]

    class Config:
        orm_mode = True

class SessionWithPayments(BaseModel):
    session: CaixaSessionRead
    payments: PaymentSummary
    
    class Config:
        orm_mode = True

class PendingInvoice(BaseModel):
    id:            int
    paciente_nome: str
    tipo:          str
    total:         float
    pendente:      float
    data_emissao:  datetime

class PendingParcela(BaseModel):
    parcela_id:    int
    paciente_nome: str
    fatura_id:     int
    numero:        int
    valor:         float
    pendente:      float
    data_vencimento: datetime

class CashierPaymentBase(BaseModel):
    fatura_id:        Optional[int]   = Field(None, description="ID da fatura paga")
    parcela_id:       Optional[int]   = Field(None, description="ID da parcela paga")
    valor_pago:       float           = Field(..., description="Valor pago")
    metodo_pagamento: str             = Field(..., description="Método: dinheiro/cartão/transferência")
    data_pagamento:   Optional[datetime] = Field(None, description="Data/hora do pagamento")
    observacoes:      Optional[str]   = Field(None, description="Observações")

class CashierPaymentCreate(CashierPaymentBase):
    pass

class CashierPaymentRead(CashierPaymentBase):
    id:           int
    operador_id:  int

    class Config:
        orm_mode = True

class CloseSessionRequest(BaseModel):
    valor_final: float = Field(..., description="Valor contado ao fechar caixa")
