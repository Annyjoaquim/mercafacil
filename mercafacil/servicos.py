"""Camada de lógica de negócio do MercaFácil."""
import hashlib
import hmac
import os
from datetime import datetime

from .db import Conexao
from .pagamentos import criar_pagamento


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


# ----------------------------------------------------------------------- vendas
class VendaServico:
    def __init__(self):
        self.bd = Conexao.obter()
        self.produtos = ProdutoServico()
        self.observadores = []

    def adicionar_observador(self, observador):
        self.observadores.append(observador)

    def _notificar(self, codigo):
        produto = self.produtos.obter_por_codigo(codigo)
        if produto["stock_actual"] <= produto["stock_minimo"]:
            for obs in self.observadores:
                obs.actualizar(produto)

    def registar_venda(self, id_utilizador, itens, metodo, valor_entregue=None,
                       desconto=0, perfil="CAIXA"):
        """itens = lista de (codigo_barras, quantidade). Devolve um resumo da venda."""
        if not itens:
            raise ErroNegocio("A venda precisa de pelo menos um produto.")
        if desconto > 0 and perfil not in ("GERENTE", "ADMIN"):
            raise ErroNegocio("Só o gerente pode aplicar desconto.")
        if desconto < 0 or desconto > 10:
            raise ErroNegocio("O desconto máximo é de 10%.")

        # junta quantidades do mesmo produto (evita vender mais do que existe)
        quantidades = {}
        for codigo, qtd in itens:
            if qtd <= 0:
                raise ErroNegocio("A quantidade deve ser maior que zero.")
            quantidades[codigo] = quantidades.get(codigo, 0) + qtd

        linhas, total_bruto = [], 0.0
        for codigo, qtd in quantidades.items():
            produto = self.produtos.obter_por_codigo(codigo)
            if produto["stock_actual"] < qtd:
                raise ErroNegocio(f"Stock insuficiente para {produto['nome']}.")
            subtotal = round(produto["preco_venda"] * qtd, 2)
            linhas.append((produto, qtd, subtotal))
            total_bruto += subtotal

        total = round(total_bruto * (1 - desconto / 100), 2)
        iva = round(total * 16 / 116, 2)   # preços já incluem IVA de 16%
        troco = criar_pagamento(metodo).processar(total, valor_entregue)

        try:
            cur = self.bd.execute(
                "INSERT INTO venda (data_hora, id_utilizador, desconto_percentagem,"
                " total, valor_iva, metodo_pagamento) VALUES (?,?,?,?,?,?)",
                (agora(), id_utilizador, desconto, total, iva, metodo.upper()),
            )
            id_venda = cur.lastrowid
            for produto, qtd, subtotal in linhas:
                self.bd.execute(
                    "INSERT INTO item_venda (id_venda, id_produto, quantidade,"
                    " preco_unitario, subtotal) VALUES (?,?,?,?,?)",
                    (id_venda, produto["id_produto"], qtd, produto["preco_venda"], subtotal),
                )
                self.bd.execute(
                    "UPDATE produto SET stock_actual = stock_actual - ? WHERE id_produto=?",
                    (qtd, produto["id_produto"]),
                )
                self.bd.execute(
                    "INSERT INTO movimento_stock (id_produto, tipo, quantidade, data_hora, motivo)"
                    " VALUES (?, 'SAIDA', ?, ?, ?)",
                    (produto["id_produto"], qtd, agora(), f"VENDA {id_venda}"),
                )
            self.bd.commit()
        except Exception:
            self.bd.rollback()
            raise

        for codigo in quantidades:
            self._notificar(codigo)
        return {"id_venda": id_venda, "total": total, "iva": iva, "troco": troco}

    def anular_venda(self, id_venda, perfil):
        if perfil not in ("GERENTE", "ADMIN"):
            raise ErroNegocio("Só o gerente pode anular vendas.")
        venda = self.bd.execute("SELECT * FROM venda WHERE id_venda=?", (id_venda,)).fetchone()
        if venda is None:
            raise ErroNegocio("Venda não encontrada.")
        if venda["estado"] == "ANULADA":
            raise ErroNegocio("Esta venda já foi anulada.")
        itens = self.bd.execute(
            "SELECT id_produto, quantidade FROM item_venda WHERE id_venda=?", (id_venda,)
        ).fetchall()
        for item in itens:
            self.bd.execute(
                "UPDATE produto SET stock_actual = stock_actual + ? WHERE id_produto=?",
                (item["quantidade"], item["id_produto"]),
            )
            self.bd.execute(
                "INSERT INTO movimento_stock (id_produto, tipo, quantidade, data_hora, motivo)"
                " VALUES (?, 'ANULACAO', ?, ?, ?)",
                (item["id_produto"], item["quantidade"], agora(), f"ANULACAO VENDA {id_venda}"),
            )
        self.bd.execute("UPDATE venda SET estado='ANULADA' WHERE id_venda=?", (id_venda,))
        self.bd.commit()


# ------------------------------------------------------------------- relatórios
class RelatorioServico:
    def __init__(self):
        self.bd = Conexao.obter()

    def resumo_do_dia(self, data):
        """data no formato AAAA-MM-DD. Conta só vendas concluídas."""
        linha = self.bd.execute(
            "SELECT COUNT(*) AS n, COALESCE(SUM(total),0) AS total, COALESCE(SUM(valor_iva),0) AS iva"
            " FROM venda WHERE estado='CONCLUIDA' AND substr(data_hora,1,10)=?",
            (data,),
        ).fetchone()
        return {"vendas": linha["n"], "total": round(linha["total"], 2), "iva": round(linha["iva"], 2)}

    def mais_vendidos(self, limite=5):
        return self.bd.execute(
            "SELECT p.nome, SUM(i.quantidade) AS vendido FROM item_venda i"
            " JOIN produto p ON p.id_produto=i.id_produto"
            " JOIN venda v ON v.id_venda=i.id_venda AND v.estado='CONCLUIDA'"
            " GROUP BY p.id_produto ORDER BY vendido DESC LIMIT ?",
            (limite,),
        ).fetchall()
