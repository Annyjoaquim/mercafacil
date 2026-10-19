"""Ligação à base de dados.

Padrão Singleton: em todo o sistema existe apenas UMA ligação aberta.
"""
import sqlite3
from pathlib import Path

CAMINHO_SCHEMA = Path(__file__).resolve().parent.parent / "sql" / "schema.sql"


class Conexao:
    _ligacao = None

    @classmethod
    def obter(cls, caminho=":memory:"):
        """Devolve a ligação; cria-a na primeira vez que é pedida."""
        if cls._ligacao is None:
            ligacao = sqlite3.connect(caminho)
            ligacao.row_factory = sqlite3.Row
            ligacao.executescript(CAMINHO_SCHEMA.read_text(encoding="utf-8"))
            cls._ligacao = ligacao
        return cls._ligacao

    @classmethod
    def fechar(cls):
        """Fecha a ligação (usado no fim do programa e nos testes)."""
        if cls._ligacao is not None:
            cls._ligacao.close()
            cls._ligacao = None
