"""Camada de lógica de negócio do MercaFácil."""
import hashlib
import hmac
import os
from datetime import datetime

from .db import Conexao


class ErroNegocio(ValueError):
    """Erro causado por violar uma regra de negócio."""


def agora():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ----------------------------------------------------------------- utilizadores
class UtilizadorServico:
    def __init__(self):
        self.bd = Conexao.obter()

    @staticmethod
    def _gerar_hash(senha, sal=None):
        sal = sal or os.urandom(8).hex()
        resumo = hashlib.pbkdf2_hmac("sha256", senha.encode(), sal.encode(), 50_000).hex()
        return f"{sal}${resumo}"

    def criar(self, nome, perfil, senha):
        if len(senha) < 6:
            raise ErroNegocio("A senha deve ter pelo menos 6 caracteres.")
        cur = self.bd.execute(
            "INSERT INTO utilizador (nome, perfil, senha_hash) VALUES (?,?,?)",
            (nome, perfil, self._gerar_hash(senha)),
        )
        self.bd.commit()
        return cur.lastrowid

    def autenticar(self, nome, senha):
        linha = self.bd.execute(
            "SELECT * FROM utilizador WHERE nome=? AND activo=1", (nome,)
        ).fetchone()
        if linha is None:
            raise ErroNegocio("Utilizador ou senha incorrectos.")
        sal, _ = linha["senha_hash"].split("$")
        if not hmac.compare_digest(linha["senha_hash"], self._gerar_hash(senha, sal)):
            raise ErroNegocio("Utilizador ou senha incorrectos.")
        return linha


# --------------------------------------------------------------------- produtos
class ProdutoServico:
    def __init__(self):
        self.bd = Conexao.obter()

    def adicionar(self, codigo, nome, preco_venda, preco_custo=0,
                  stock_minimo=5, id_categoria=None):
        if preco_venda <= 0:
            raise ErroNegocio("O preço de venda deve ser maior que zero.")
        existe = self.bd.execute(
            "SELECT 1 FROM produto WHERE codigo_barras=?", (codigo,)
        ).fetchone()
        if existe:
            raise ErroNegocio("Já existe um produto com este código de barras.")
        cur = self.bd.execute(
            "INSERT INTO produto (codigo_barras, nome, id_categoria, preco_venda,"
            " preco_custo, stock_minimo) VALUES (?,?,?,?,?,?)",
            (codigo, nome, id_categoria, preco_venda, preco_custo, stock_minimo),
        )
        self.bd.commit()
        return cur.lastrowid

    def obter_por_codigo(self, codigo):
        linha = self.bd.execute(
            "SELECT * FROM produto WHERE codigo_barras=?", (codigo,)
        ).fetchone()
        if linha is None:
            raise ErroNegocio("Produto não encontrado.")
        return linha

    def dar_entrada(self, id_produto, quantidade, motivo="ENTRADA MANUAL"):
        if quantidade <= 0:
            raise ErroNegocio("A quantidade deve ser maior que zero.")
        self.bd.execute(
            "UPDATE produto SET stock_actual = stock_actual + ? WHERE id_produto=?",
            (quantidade, id_produto),
        )
        self.bd.execute(
            "INSERT INTO movimento_stock (id_produto, tipo, quantidade, data_hora, motivo)"
            " VALUES (?, 'ENTRADA', ?, ?, ?)",
            (id_produto, quantidade, agora(), motivo),
        )
        self.bd.commit()

    def registar_compra(self, id_fornecedor, itens):
        """itens = lista de (id_produto, quantidade, preco_custo)."""
        if not itens:
            raise ErroNegocio("A compra precisa de pelo menos um produto.")
        total = round(sum(q * c for _, q, c in itens), 2)
        cur = self.bd.execute(
            "INSERT INTO compra (id_fornecedor, data_compra, total) VALUES (?,?,?)",
            (id_fornecedor, agora(), total),
        )
        id_compra = cur.lastrowid
        for id_produto, qtd, custo in itens:
            self.bd.execute(
                "INSERT INTO item_compra (id_compra, id_produto, quantidade, preco_custo)"
                " VALUES (?,?,?,?)",
                (id_compra, id_produto, qtd, custo),
            )
            self.dar_entrada(id_produto, qtd, motivo=f"COMPRA {id_compra}")
        self.bd.commit()
        return id_compra

    def stock_baixo(self):
        return self.bd.execute(
            "SELECT * FROM produto WHERE stock_actual <= stock_minimo ORDER BY nome"
        ).fetchall()


