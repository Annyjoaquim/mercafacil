"""Testes de integração: verificam várias peças a trabalhar juntas (serviço + base de dados)."""
from mercafacil.alertas import AlertaStockBaixo
from mercafacil.servicos import ErroNegocio
from tests.base import BaseTeste


class TestesIntegracao(BaseTeste):
    def test_TI01_venda_reduz_stock_e_regista_movimento(self):
        r = self.vendas.registar_venda(self.id_caixa, [("7001001", 3)], "DINHEIRO", valor_entregue=300)
        self.assertEqual(r["total"], 255.0)
        self.assertEqual(r["troco"], 45.0)
        self.assertEqual(self.stock(self.arroz), 97)
        n = self.bd.execute("SELECT COUNT(*) FROM movimento_stock WHERE tipo='SAIDA'").fetchone()[0]
        self.assertEqual(n, 1)

    def test_TI02_stock_insuficiente_nao_altera_nada(self):
        with self.assertRaises(ErroNegocio):
            self.vendas.registar_venda(self.id_caixa, [("7001001", 500)], "MPESA")
        self.assertEqual(self.stock(self.arroz), 100)
        self.assertEqual(self.bd.execute("SELECT COUNT(*) FROM venda").fetchone()[0], 0)

    def test_TI03_anular_venda_repoe_stock(self):
        r = self.vendas.registar_venda(self.id_caixa, [("7001001", 10)], "EMOLA")
        self.vendas.anular_venda(r["id_venda"], perfil="GERENTE")
        self.assertEqual(self.stock(self.arroz), 100)

    def test_TI04_stock_baixo_dispara_alerta(self):
        alerta = AlertaStockBaixo()
        self.vendas.adicionar_observador(alerta)
        self.vendas.registar_venda(self.id_caixa, [("7001001", 85)], "CARTAO")  # fica com 15 (< 20)
        self.assertEqual(len(alerta.mensagens), 1)
        self.assertIn("Arroz 1 kg", alerta.mensagens[0])
