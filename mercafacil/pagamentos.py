"""Formas de pagamento.

Padrão Factory: a função criar_pagamento() decide qual classe usar,
de modo que o resto do sistema não precisa de conhecer cada método.
Nota: M-Pesa, e-Mola e cartão são SIMULADOS (não há ligação real aos operadores).
"""


class ErroPagamento(ValueError):
    pass


class Pagamento:
    nome = ""

    def processar(self, total, valor_entregue=None):
        """Devolve o troco (0 se não houver)."""
        raise NotImplementedError


class PagamentoDinheiro(Pagamento):
    nome = "DINHEIRO"

    def processar(self, total, valor_entregue=None):
        if valor_entregue is None or valor_entregue < total:
            raise ErroPagamento("Valor entregue insuficiente.")
        return round(valor_entregue - total, 2)


class PagamentoElectronico(Pagamento):
    """M-Pesa, e-Mola e cartão: paga-se o valor exacto, sem troco."""

    def processar(self, total, valor_entregue=None):
        return 0.0


class PagamentoMPesa(PagamentoElectronico):
    nome = "MPESA"


class PagamentoEMola(PagamentoElectronico):
    nome = "EMOLA"


class PagamentoCartao(PagamentoElectronico):
    nome = "CARTAO"


_METODOS = {
    "DINHEIRO": PagamentoDinheiro,
    "MPESA": PagamentoMPesa,
    "EMOLA": PagamentoEMola,
    "CARTAO": PagamentoCartao,
}


def criar_pagamento(metodo):
    """Fábrica: recebe o nome do método e devolve o objecto certo."""
    try:
        return _METODOS[metodo.upper()]()
    except KeyError:
        raise ErroPagamento(f"Método de pagamento desconhecido: {metodo}")
