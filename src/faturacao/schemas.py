from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
import enum


class FaturaTipo(str, enum.Enum):
    consulta = "consulta"
    plano    = "plano"


class FaturaEstado(str, enum.Enum):
    pendente  = "pendente"
    parcial   = "parcial"
    paga      = "paga"
    cancelada = "cancelada"


class ParcelaEstado(str, enum.Enum):
    pendente = "pendente"
    parcial  = "parcial"
    paga     = "paga"


class MetodoPagamento(str, enum.Enum):
    dinheiro = "dinheiro"
    cartao   = "cartao"
    transferencia = "transferencia"
    


# -------------------- Fatura --------------------

class FaturaBase(BaseModel):
    paciente_id:  int                = Field(..., description="ID do paciente")
    tipo:         FaturaTipo         = Field(..., description="Tipo: consulta ou plano")
    consulta_id:  Optional[int]      = Field(None, description="ID da consulta (se for fatura de consulta)")
    plano_id:     Optional[int]      = Field(None, description="ID do plano (se for fatura de plano)")


class FaturaCreate(FaturaBase):
    pass  # total e estado serão calculados/definidos pelo servidor


class FaturaItemBase(BaseModel):
    origem_tipo:    str             = Field(..., description="‘consulta_item’ ou ‘plano_item’")
    origem_id:      int             = Field(..., description="ID do item de origem")
    quantidade:     Optional[int]   = Field(1, description="Número de unidades")
    preco_unitario: float           = Field(..., description="Preço unitário para este item")
    descricao:      Optional[str]   = Field(None, description="Descrição do item (opcional)")

class FaturaItemCreate(FaturaItemBase):
    pass


class ParcelaBase(BaseModel):
    numero:           int                  = Field(..., description="Número sequencial da parcela")
    valor_planejado:  float                = Field(..., description="Valor previsto para a parcela")
    data_vencimento:  Optional[datetime]   = Field(None, description="Data de vencimento da parcela")


class ParcelaCreate(ParcelaBase):
    pass


# -------------------- Reads --------------------

class ParcelaRead(ParcelaBase):
    id:              int
    valor_pago:      Optional[float]       = Field(None, description="Valor realmente pago")
    data_pagamento:  Optional[datetime]    = Field(None, description="Quando foi pago")
    estado:          ParcelaEstado
    metodo_pagamento: Optional[MetodoPagamento] = Field(None, description="Método de pagamento utilizado")

    class Config:
        from_attributes = True


class ParcelaPagamentoRequest(BaseModel):
    valor_pago: float = Field(..., description="Valor sendo pago")
    metodo_pagamento: MetodoPagamento = Field(..., description="Método de pagamento")
    data_pagamento: Optional[datetime] = Field(None, description="Data do pagamento (padrão: agora)")


class FaturaItemRead(FaturaItemBase):
    id:    int    = Field(..., description="ID do item de fatura")
    total: float  = Field(..., description="quantidade × preço_unitario")
    descricao: str = Field("Item sem descrição", description="Descrição do procedimento ou artigo")

    class Config:
        from_attributes = True


class FaturaPagamentoRead(BaseModel):
    id: int
    fatura_id: int
    valor: float
    data_pagamento: datetime
    metodo_pagamento: MetodoPagamento
    observacoes: Optional[str] = None

    class Config:
        orm_mode = True

class FaturaRead(FaturaBase):
    id:           int
    data_emissao: datetime           = Field(..., description="Quando a fatura foi emitida")
    total:        float               = Field(..., description="Soma de todos os itens")
    estado:       FaturaEstado

    itens:    List[FaturaItemRead]   = []
    parcelas: List[ParcelaRead]      = []
    pagamentos: List[FaturaPagamentoRead] = []

    class Config:
        from_attributes = True
