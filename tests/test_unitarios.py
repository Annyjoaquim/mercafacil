"""Testes unitários: verificam uma única peça de cada vez."""
import unittest

from mercafacil.pagamentos import ErroPagamento, PagamentoDinheiro, criar_pagamento
from mercafacil.servicos import ErroNegocio, UtilizadorServico
from tests.base import BaseTeste


class TestesUnitarios(BaseTeste):
    def test_TU01_preco_zero_e_rejeitado(self):
        with self.assertRaises(ErroNegocio):
            self.produtos.adicionar("999", "Produto inválido", 0)

    def test_TU02_dinheiro_calcula_troco(self):
        self.assertEqual(PagamentoDinheiro().processar(total=120.0, valor_entregue=200.0), 80.0)

    def test_TU03_dinheiro_insuficiente_e_rejeitado(self):
        with self.assertRaises(ErroPagamento):
            PagamentoDinheiro().processar(total=120.0, valor_entregue=100.0)

    def test_TU04_fabrica_rejeita_metodo_desconhecido(self):
        with self.assertRaises(ErroPagamento):
            criar_pagamento("CHEQUE")

    def test_TU05_senha_errada_nao_entra(self):
        with self.assertRaises(ErroNegocio):
            UtilizadorServico().autenticar("ana.caixa", "errada")


if __name__ == "__main__":
    unittest.main()
