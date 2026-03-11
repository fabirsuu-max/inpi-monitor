import sqlite3
import os
from .models import MarcaMonitorada

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "monitor.db")


def _connect():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS marcas_monitoradas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                termo TEXT NOT NULL,
                tipo_busca TEXT NOT NULL DEFAULT 'nome',
                observacao TEXT DEFAULT '',
                ativo INTEGER DEFAULT 1
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS historico (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                marca_id INTEGER,
                numero_processo TEXT,
                marca_nome TEXT,
                titular TEXT,
                despacho TEXT,
                data_verificacao TEXT,
                FOREIGN KEY(marca_id) REFERENCES marcas_monitoradas(id)
            )
        """)
        conn.commit()


def listar_monitoradas() -> list[MarcaMonitorada]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM marcas_monitoradas ORDER BY termo"
        ).fetchall()
    return [MarcaMonitorada(
        id=r["id"], termo=r["termo"], tipo_busca=r["tipo_busca"],
        observacao=r["observacao"], ativo=bool(r["ativo"])
    ) for r in rows]


def adicionar_monitorada(marca: MarcaMonitorada) -> int:
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO marcas_monitoradas (termo, tipo_busca, observacao, ativo) VALUES (?,?,?,?)",
            (marca.termo, marca.tipo_busca, marca.observacao, int(marca.ativo))
        )
        conn.commit()
        return cur.lastrowid


def atualizar_monitorada(marca: MarcaMonitorada):
    with _connect() as conn:
        conn.execute(
            "UPDATE marcas_monitoradas SET termo=?, tipo_busca=?, observacao=?, ativo=? WHERE id=?",
            (marca.termo, marca.tipo_busca, marca.observacao, int(marca.ativo), marca.id)
        )
        conn.commit()


def remover_monitorada(marca_id: int):
    with _connect() as conn:
        conn.execute("DELETE FROM marcas_monitoradas WHERE id=?", (marca_id,))
        conn.execute("DELETE FROM historico WHERE marca_id=?", (marca_id,))
        conn.commit()


def salvar_historico(marca_id: int, processos: list):
    from datetime import datetime
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _connect() as conn:
        for p in processos:
            conn.execute(
                """INSERT INTO historico (marca_id, numero_processo, marca_nome, titular, despacho, data_verificacao)
                   VALUES (?,?,?,?,?,?)""",
                (marca_id, p.numero, p.marca_nome, p.titular_principal, p.despacho_nome, agora)
            )
        conn.commit()


def listar_historico(marca_id: int) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM historico WHERE marca_id=? ORDER BY data_verificacao DESC LIMIT 200",
            (marca_id,)
        ).fetchall()
    return [dict(r) for r in rows]
