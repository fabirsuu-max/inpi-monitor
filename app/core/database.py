import json
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
                criterios TEXT DEFAULT NULL,
                observacao TEXT DEFAULT '',
                ativo INTEGER DEFAULT 1
            )
        """)
        # Migration: add criterios column to existing DBs
        cols = [r[1] for r in conn.execute("PRAGMA table_info(marcas_monitoradas)").fetchall()]
        if "criterios" not in cols:
            conn.execute("ALTER TABLE marcas_monitoradas ADD COLUMN criterios TEXT DEFAULT NULL")
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


def _row_to_marca(r) -> MarcaMonitorada:
    criterios = {}
    if r["criterios"]:
        try:
            criterios = json.loads(r["criterios"])
        except (json.JSONDecodeError, TypeError):
            pass
    # Backward compat: convert old termo/tipo_busca records
    if not criterios and r["termo"] and r["tipo_busca"]:
        tipo = r["tipo_busca"]
        if tipo == "regex":
            criterios = {"nome": r["termo"], "use_regex": True}
        else:
            criterios = {tipo: r["termo"]}
    return MarcaMonitorada(
        id=r["id"],
        termo=r["termo"],
        tipo_busca=r["tipo_busca"],
        criterios=criterios,
        observacao=r["observacao"] or "",
        ativo=bool(r["ativo"]),
    )


def listar_monitoradas() -> list[MarcaMonitorada]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM marcas_monitoradas ORDER BY termo"
        ).fetchall()
    return [_row_to_marca(r) for r in rows]


def adicionar_monitorada(marca: MarcaMonitorada) -> int:
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO marcas_monitoradas (termo, tipo_busca, criterios, observacao, ativo) VALUES (?,?,?,?,?)",
            (marca.termo, marca.tipo_busca, json.dumps(marca.criterios), marca.observacao, int(marca.ativo))
        )
        conn.commit()
        return cur.lastrowid


def atualizar_monitorada(marca: MarcaMonitorada):
    with _connect() as conn:
        conn.execute(
            "UPDATE marcas_monitoradas SET termo=?, tipo_busca=?, criterios=?, observacao=?, ativo=? WHERE id=?",
            (marca.termo, marca.tipo_busca, json.dumps(marca.criterios), marca.observacao, int(marca.ativo), marca.id)
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
