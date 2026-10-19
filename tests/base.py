import unittest

from mercafacil.db import Conexao
from mercafacil.servicos import ProdutoServico, UtilizadorServico, VendaServico


class BaseTeste(unittest.TestCase):
    """Prepara uma base de dados nova (em memória) antes de cada teste."""

    def setUp(self):
        Conexao.fechar()
        self.bd = Conexao.obter()
        self.produtos = ProdutoServico()
        self.vendas = VendaServico()
        self.id_caixa = UtilizadorServico().criar("ana.caixa", "CAIXA", "senha123")
        self.arroz = self.produtos.adicionar("7001001", "Arroz 1 kg", 85.00, 70.00, stock_minimo=20)
        self.agua = self.produtos.adicionar("7002001", "Água 1,5 L", 40.00, 30.00, stock_minimo=40)
        self.produtos.dar_entrada(self.arroz, 100)
        self.produtos.dar_entrada(self.agua, 50)

    def tearDown(self):
        Conexao.fechar()

    def stock(self, id_produto):
        return self.bd.execute(
            "SELECT stock_actual FROM produto WHERE id_produto=?", (id_produto,)
        ).fetchone()[0]
