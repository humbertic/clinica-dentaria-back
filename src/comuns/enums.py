import enum

class MetodoPagamento(enum.Enum):
    dinheiro = "dinheiro"
    cartao = "cartao"
    transferencia = "transferencia"
    