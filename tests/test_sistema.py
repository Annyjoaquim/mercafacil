"""Testes de sistema/aceitação: simulam o que o utilizador faz num dia real de trabalho.
(Automatizados ao nível dos serviços, sem ecrãs.)"""
from datetime import datetime

from mercafacil.servicos import ErroNegocio, RelatorioServico
from tests.base import BaseTeste


class TestesSistema(BaseTeste):
    def test_TS01_dia_de_trabalho_completo(self):
        """Recebe mercadoria, vende com 3 métodos e confere o fecho do dia."""
        self.produtos.dar_entrada(self.agua, 100, motivo="COMPRA FORNECEDOR")
        self.vendas.registar_venda(self.id_caixa, [("7001001", 2), ("7002001", 5)], "DINHEIRO", valor_entregue=400)
        self.vendas.registar_venda(self.id_caixa, [("7002001", 10)], "MPESA")
        self.vendas.registar_venda(self.id_caixa, [("7001001", 1)], "EMOLA")
        hoje = datetime.now().strftime("%Y-%m-%d")
        resumo = RelatorioServico().resumo_do_dia(hoje)
        self.assertEqual(resumo["vendas"], 3)
        self.assertEqual(resumo["total"], 370.0 + 400.0 + 85.0)
        self.assertEqual(self.stock(self.agua), 50 + 100 - 5 - 10)

    def test_TS02_regras_de_permissao_do_desconto_e_anulacao(self):
        """Caixa não dá desconto nem anula; gerente pode (até 10%)."""
        with self.assertRaises(ErroNegocio):
            self.vendas.registar_venda(self.id_caixa, [("7001001", 1)], "MPESA", desconto=5, perfil="CAIXA")
        r = self.vendas.registar_venda(self.id_caixa, [("7001001", 1)], "MPESA", desconto=10, perfil="GERENTE")
        self.assertEqual(r["total"], 76.5)
        with self.assertRaises(ErroNegocio):
            self.vendas.anular_venda(r["id_venda"], perfil="CAIXA")
        with self.assertRaises(ErroNegocio):
            self.vendas.registar_venda(self.id_caixa, [("7001001", 1)], "MPESA", desconto=15, perfil="GERENTE")
