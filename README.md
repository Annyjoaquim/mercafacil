# MercaFácil

Sistema simples de gestão de loja/supermercado (projecto de Engenharia de Software — ISDB).

Funcionalidades do núcleo: produtos, stock, compras a fornecedores, vendas (dinheiro, M-Pesa, e-Mola, cartão),
anulação de vendas, alertas de stock baixo, utilizadores com perfis e relatório do dia.

## Como correr os testes
```
python3 -m unittest discover -s tests -t . -v
```

## Estrutura
- `mercafacil/` — código (db, pagamentos, alertas, servicos)
- `sql/` — esquema da base de dados e dados de exemplo
- `tests/` — testes unitários, de integração e de sistema
