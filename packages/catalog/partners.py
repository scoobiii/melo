"""CRM básico — parceiros de negócio (gravadora/produtor/plataforma).
Mesmo SQLite do resto do catalog, sem dependência externa. Odoo/ERP
externo fica adiado pra quando existir faturamento real a declarar
(ver docs/GAPS_NEGOCIO.md)."""
import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS parceiros_negocio (
    id INTEGER PRIMARY KEY,
    nome TEXT NOT NULL,
    tipo TEXT CHECK(tipo IN ('gravadora', 'produtor_independente', 'plataforma')),
    status TEXT CHECK(status IN ('lead', 'em_negociacao', 'contrato_assinado', 'ativo')) DEFAULT 'lead',
    contato TEXT,
    observacoes TEXT,
    criado_em TEXT DEFAULT (datetime('now'))
);
"""


def init_partners_schema(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def create_partner(db_path: str, nome: str, tipo: str, contato: str = "", observacoes: str = "") -> int:
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute(
            "INSERT INTO parceiros_negocio (nome, tipo, contato, observacoes) VALUES (?, ?, ?, ?)",
            (nome, tipo, contato, observacoes),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def update_partner_status(db_path: str, partner_id: int, status: str) -> None:
    valid = {"lead", "em_negociacao", "contrato_assinado", "ativo"}
    if status not in valid:
        raise ValueError(f"status inválido: {status!r} — esperado um de {valid}")
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "UPDATE parceiros_negocio SET status = ? WHERE id = ?",
            (status, partner_id),
        )
        conn.commit()
    finally:
        conn.close()


def list_partners(db_path: str, status: str | None = None) -> list[dict]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        if status:
            rows = conn.execute(
                "SELECT * FROM parceiros_negocio WHERE status = ? ORDER BY criado_em DESC",
                (status,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM parceiros_negocio ORDER BY criado_em DESC"
            ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
