"""Alertas de stock baixo.

Padrão Observer: o serviço de vendas "avisa" os observadores
sempre que um produto fica com stock igual ou abaixo do mínimo.
"""


class Observador:
    def actualizar(self, produto):
        raise NotImplementedError


class AlertaStockBaixo(Observador):
    def __init__(self):
        self.mensagens = []

    def actualizar(self, produto):
        self.mensagens.append(
            f"Stock baixo: {produto['nome']} "
            f"({produto['stock_actual']} un., mínimo {produto['stock_minimo']})"
        )
