-- MercaFácil - Dados de exemplo (para demonstração e defesa)
INSERT INTO categoria (nome) VALUES ('Mercearia'), ('Bebidas'), ('Higiene e Limpeza'), ('Padaria');

INSERT INTO fornecedor (nome, contacto, nuit) VALUES
 ('Distribuidora Maputo Lda', '84 000 0001', '400000001'),
 ('Bebidas do Sul Lda',       '82 000 0002', '400000002');

-- As senhas reais são guardadas em formato seguro pela aplicação (ver UtilizadorServico).
INSERT INTO utilizador (nome, perfil, senha_hash) VALUES
 ('ana.caixa',   'CAIXA',   'exemplo'),
 ('paulo.stock', 'STOCK',   'exemplo'),
 ('maria.gerente','GERENTE','exemplo');

INSERT INTO produto (codigo_barras, nome, id_categoria, preco_venda, preco_custo, stock_actual, stock_minimo) VALUES
 ('7001001', 'Arroz 1 kg',           1,  85.00,  70.00, 120, 20),
 ('7001002', 'Óleo alimentar 1 L',   1, 150.00, 125.00,  60, 15),
 ('7002001', 'Água mineral 1,5 L',   2,  40.00,  30.00, 200, 40),
 ('7002002', 'Refresco 500 ml',      2,  55.00,  42.00,  90, 25),
 ('7003001', 'Sabão em barra',       3,  30.00,  22.00,  80, 20),
 ('7004001', 'Pão (unidade)',        4,   5.00,   3.00, 300, 50);
