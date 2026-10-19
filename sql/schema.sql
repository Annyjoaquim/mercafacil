-- MercaFácil - Esquema da base de dados (compatível com SQLite; adaptável a MySQL)
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS categoria (
    id_categoria INTEGER PRIMARY KEY AUTOINCREMENT,
    nome         TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS fornecedor (
    id_fornecedor INTEGER PRIMARY KEY AUTOINCREMENT,
    nome          TEXT NOT NULL,
    contacto      TEXT,
    nuit          TEXT
);

CREATE TABLE IF NOT EXISTS utilizador (
    id_utilizador INTEGER PRIMARY KEY AUTOINCREMENT,
    nome          TEXT NOT NULL UNIQUE,
    perfil        TEXT NOT NULL CHECK (perfil IN ('CAIXA','STOCK','GERENTE','ADMIN')),
    senha_hash    TEXT NOT NULL,
    activo        INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS produto (
    id_produto    INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_barras TEXT NOT NULL UNIQUE,
    nome          TEXT NOT NULL,
    id_categoria  INTEGER REFERENCES categoria(id_categoria),
    preco_venda   REAL NOT NULL CHECK (preco_venda > 0),
    preco_custo   REAL NOT NULL DEFAULT 0 CHECK (preco_custo >= 0),
    stock_actual  INTEGER NOT NULL DEFAULT 0 CHECK (stock_actual >= 0),
    stock_minimo  INTEGER NOT NULL DEFAULT 5
);

CREATE TABLE IF NOT EXISTS venda (
    id_venda             INTEGER PRIMARY KEY AUTOINCREMENT,
    data_hora            TEXT NOT NULL,
    id_utilizador        INTEGER NOT NULL REFERENCES utilizador(id_utilizador),
    desconto_percentagem REAL NOT NULL DEFAULT 0,
    total                REAL NOT NULL,
    valor_iva            REAL NOT NULL,
    metodo_pagamento     TEXT NOT NULL CHECK (metodo_pagamento IN ('DINHEIRO','MPESA','EMOLA','CARTAO')),
    estado               TEXT NOT NULL DEFAULT 'CONCLUIDA' CHECK (estado IN ('CONCLUIDA','ANULADA'))
);

CREATE TABLE IF NOT EXISTS item_venda (
    id_item        INTEGER PRIMARY KEY AUTOINCREMENT,
    id_venda       INTEGER NOT NULL REFERENCES venda(id_venda),
    id_produto     INTEGER NOT NULL REFERENCES produto(id_produto),
    quantidade     INTEGER NOT NULL CHECK (quantidade > 0),
    preco_unitario REAL NOT NULL,
    subtotal       REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS compra (
    id_compra     INTEGER PRIMARY KEY AUTOINCREMENT,
    id_fornecedor INTEGER NOT NULL REFERENCES fornecedor(id_fornecedor),
    data_compra   TEXT NOT NULL,
    total         REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS item_compra (
    id_item_compra INTEGER PRIMARY KEY AUTOINCREMENT,
    id_compra      INTEGER NOT NULL REFERENCES compra(id_compra),
    id_produto     INTEGER NOT NULL REFERENCES produto(id_produto),
    quantidade     INTEGER NOT NULL CHECK (quantidade > 0),
    preco_custo    REAL NOT NULL CHECK (preco_custo >= 0)
);

CREATE TABLE IF NOT EXISTS movimento_stock (
    id_movimento INTEGER PRIMARY KEY AUTOINCREMENT,
    id_produto   INTEGER NOT NULL REFERENCES produto(id_produto),
    tipo         TEXT NOT NULL CHECK (tipo IN ('ENTRADA','SAIDA','ANULACAO','AJUSTE')),
    quantidade   INTEGER NOT NULL,
    data_hora    TEXT NOT NULL,
    motivo       TEXT
);
