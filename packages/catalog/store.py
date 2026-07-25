# Localização no repo: packages/catalog/store.py
"""
Persistência de artistas de origem/destino e mapeamento de segmentos.

Usa sqlite3 da stdlib de propósito: nenhuma dependência nova, nenhuma
compilação nativa. Isso importa neste projeto porque já tivemos dor real
com pacotes que exigem build nativo (torch, anthropic/jiter) no ambiente
Termux/Android. SQLite roda em qualquer lugar sem esse risco.

Modelo de dados:
- source_artists: quem fez a faixa original (origem: panamá etc.)
- destination_artists: candidatos locais por gênero de destino (brasil)
- segment_mappings: liga um segmento de uma faixa a um artista de destino
  e registra que tipo de transformação foi aplicada (direta ou criativa)

Este módulo é a peça que faltava para o pipeline deixar de perder estado
entre execuções — hoje o pipeline só grava JSON solto em output/.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional

DEFAULT_DB_PATH = Path("datasets/melo_catalog.sqlite3")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS source_artists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    genero_origem TEXT NOT NULL,
    pais TEXT,
    faixa_original TEXT,
    status_licenca TEXT NOT NULL DEFAULT 'nao_verificado',
    UNIQUE(nome, faixa_original)
);

CREATE TABLE IF NOT EXISTS destination_artists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    genero_destino TEXT NOT NULL,
    regiao TEXT,
    perfil_vocal TEXT,
    disponivel INTEGER NOT NULL DEFAULT 1,
    UNIQUE(nome, genero_destino)
);

CREATE TABLE IF NOT EXISTS segment_mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    faixa_id TEXT NOT NULL,
    segmento_indice INTEGER NOT NULL,
    segmento_tipo TEXT NOT NULL,  -- 'verso', 'refrao', 'ponte', etc.
    source_artist_id INTEGER REFERENCES source_artists(id),
    destination_artist_id INTEGER REFERENCES destination_artists(id),
    tipo_transformacao TEXT NOT NULL DEFAULT 'direta',  -- 'direta' | 'criativa'
    UNIQUE(faixa_id, segmento_indice)
);
"""


@dataclass(frozen=True)
class SourceArtist:
    id: int
    nome: str
    genero_origem: str
    pais: Optional[str]
    faixa_original: Optional[str]
    status_licenca: str


@dataclass(frozen=True)
class DestinationArtist:
    id: int
    nome: str
    genero_destino: str
    regiao: Optional[str]
    perfil_vocal: Optional[str]
    disponivel: bool


@dataclass(frozen=True)
class SegmentMapping:
    id: int
    faixa_id: str
    segmento_indice: int
    segmento_tipo: str
    source_artist_id: Optional[int]
    destination_artist_id: Optional[int]
    tipo_transformacao: str


class CatalogStore:
    """Acesso ao catálogo de artistas e mapeamentos. Uma instância por
    conexão de banco; seguro chamar `CatalogStore(path)` várias vezes
    (schema é criado com IF NOT EXISTS, idempotente).
    """

    def __init__(self, db_path: Path | str = DEFAULT_DB_PATH):
        self._db_path = Path(db_path) if str(db_path) != ":memory:" else None
        self._is_memory = str(db_path) == ":memory:"
        self._memory_conn: sqlite3.Connection | None = None

        if not self._is_memory:
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            # :memory: cria um banco NOVO a cada connect() — precisa manter
            # uma única conexão viva pela vida do objeto, ou o schema some
            # entre chamadas.
            self._memory_conn = sqlite3.connect(":memory:")
            self._memory_conn.execute("PRAGMA foreign_keys = ON")
            self._memory_conn.row_factory = sqlite3.Row

        self._init_schema()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        if self._is_memory:
            # Reusa a mesma conexão; não fecha (fechar destruiria o banco).
            yield self._memory_conn
            self._memory_conn.commit()
            return

        conn = sqlite3.connect(self._db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(_SCHEMA)

    # ---- source artists ----

    def add_source_artist(
        self,
        nome: str,
        genero_origem: str,
        pais: str | None = None,
        faixa_original: str | None = None,
        status_licenca: str = "nao_verificado",
    ) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                """INSERT INTO source_artists
                   (nome, genero_origem, pais, faixa_original, status_licenca)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(nome, faixa_original) DO UPDATE SET
                       genero_origem=excluded.genero_origem,
                       pais=excluded.pais,
                       status_licenca=excluded.status_licenca
                   RETURNING id""",
                (nome, genero_origem, pais, faixa_original, status_licenca),
            )
            return cur.fetchone()["id"]

    def list_source_artists(self, genero_origem: str | None = None) -> list[SourceArtist]:
        query = "SELECT * FROM source_artists"
        params: tuple = ()
        if genero_origem:
            query += " WHERE genero_origem = ?"
            params = (genero_origem,)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [SourceArtist(**dict(r)) for r in rows]

    # ---- destination artists ----

    def add_destination_artist(
        self,
        nome: str,
        genero_destino: str,
        regiao: str | None = None,
        perfil_vocal: str | None = None,
        disponivel: bool = True,
    ) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                """INSERT INTO destination_artists
                   (nome, genero_destino, regiao, perfil_vocal, disponivel)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(nome, genero_destino) DO UPDATE SET
                       regiao=excluded.regiao,
                       perfil_vocal=excluded.perfil_vocal,
                       disponivel=excluded.disponivel
                   RETURNING id""",
                (nome, genero_destino, regiao, perfil_vocal, int(disponivel)),
            )
            return cur.fetchone()["id"]

    def list_destination_artists(
        self, genero_destino: str | None = None, apenas_disponiveis: bool = True
    ) -> list[DestinationArtist]:
        query = "SELECT * FROM destination_artists WHERE 1=1"
        params: list = []
        if genero_destino:
            query += " AND genero_destino = ?"
            params.append(genero_destino)
        if apenas_disponiveis:
            query += " AND disponivel = 1"
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [
            DestinationArtist(
                id=r["id"],
                nome=r["nome"],
                genero_destino=r["genero_destino"],
                regiao=r["regiao"],
                perfil_vocal=r["perfil_vocal"],
                disponivel=bool(r["disponivel"]),
            )
            for r in rows
        ]

    # ---- segment mappings ----

    def map_segment(
        self,
        faixa_id: str,
        segmento_indice: int,
        segmento_tipo: str,
        destination_artist_id: int | None = None,
        source_artist_id: int | None = None,
        tipo_transformacao: str = "direta",
    ) -> int:
        if tipo_transformacao not in ("direta", "criativa"):
            raise ValueError(
                "tipo_transformacao deve ser 'direta' ou 'criativa', "
                f"recebido: {tipo_transformacao!r}"
            )
        with self._connect() as conn:
            cur = conn.execute(
                """INSERT INTO segment_mappings
                   (faixa_id, segmento_indice, segmento_tipo,
                    source_artist_id, destination_artist_id, tipo_transformacao)
                   VALUES (?, ?, ?, ?, ?, ?)
                   ON CONFLICT(faixa_id, segmento_indice) DO UPDATE SET
                       segmento_tipo=excluded.segmento_tipo,
                       source_artist_id=excluded.source_artist_id,
                       destination_artist_id=excluded.destination_artist_id,
                       tipo_transformacao=excluded.tipo_transformacao
                   RETURNING id""",
                (
                    faixa_id,
                    segmento_indice,
                    segmento_tipo,
                    source_artist_id,
                    destination_artist_id,
                    tipo_transformacao,
                ),
            )
            return cur.fetchone()["id"]

    def list_mappings_for_faixa(self, faixa_id: str) -> list[SegmentMapping]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM segment_mappings WHERE faixa_id = ? ORDER BY segmento_indice",
                (faixa_id,),
            ).fetchall()
        return [SegmentMapping(**dict(r)) for r in rows]
