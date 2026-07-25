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

import json
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

CREATE TABLE IF NOT EXISTS produtores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL UNIQUE,
    genero_atuacao TEXT,
    regiao TEXT,
    contato TEXT
);

CREATE TABLE IF NOT EXISTS faixas (
    id TEXT PRIMARY KEY,
    caminho_audio TEXT NOT NULL,
    genero_origem TEXT NOT NULL,
    duracao_segundos REAL,
    bpm REAL,
    instrumentos TEXT,
    partitura_path TEXT,
    source_artist_id INTEGER REFERENCES source_artists(id),
    produtor_id INTEGER REFERENCES produtores(id),
    criado_em TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS vozes_detectadas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    faixa_id TEXT NOT NULL REFERENCES faixas(id),
    segmento_indice INTEGER,
    perfil_vocal TEXT,
    genero_vocal TEXT,
    confianca REAL
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


@dataclass(frozen=True)
class Produtor:
    id: int
    nome: str
    genero_atuacao: Optional[str]
    regiao: Optional[str]
    contato: Optional[str]


@dataclass(frozen=True)
class Faixa:
    id: str
    caminho_audio: str
    genero_origem: str
    duracao_segundos: Optional[float]
    bpm: Optional[float]
    instrumentos: list
    partitura_path: Optional[str]
    source_artist_id: Optional[int]
    produtor_id: Optional[int]
    criado_em: str


@dataclass(frozen=True)
class VozDetectada:
    id: int
    faixa_id: str
    segmento_indice: Optional[int]
    perfil_vocal: Optional[str]
    genero_vocal: Optional[str]
    confianca: Optional[float]


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

    # ---- produtores ----

    def add_produtor(
        self,
        nome: str,
        genero_atuacao: str | None = None,
        regiao: str | None = None,
        contato: str | None = None,
    ) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                """INSERT INTO produtores (nome, genero_atuacao, regiao, contato)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(nome) DO UPDATE SET
                       genero_atuacao=excluded.genero_atuacao,
                       regiao=excluded.regiao,
                       contato=excluded.contato
                   RETURNING id""",
                (nome, genero_atuacao, regiao, contato),
            )
            return cur.fetchone()["id"]

    def list_produtores(self, genero_atuacao: str | None = None) -> list[Produtor]:
        query = "SELECT * FROM produtores"
        params: tuple = ()
        if genero_atuacao:
            query += " WHERE genero_atuacao = ?"
            params = (genero_atuacao,)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [Produtor(**dict(r)) for r in rows]

    # ---- faixas ----

    def add_faixa(
        self,
        id: str,
        caminho_audio: str,
        genero_origem: str,
        duracao_segundos: float | None = None,
        bpm: float | None = None,
        instrumentos: list[str] | None = None,
        partitura_path: str | None = None,
        source_artist_id: int | None = None,
        produtor_id: int | None = None,
    ) -> str:
        instrumentos_json = json.dumps(instrumentos or [])
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO faixas
                   (id, caminho_audio, genero_origem, duracao_segundos, bpm,
                    instrumentos, partitura_path, source_artist_id, produtor_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(id) DO UPDATE SET
                       caminho_audio=excluded.caminho_audio,
                       genero_origem=excluded.genero_origem,
                       duracao_segundos=excluded.duracao_segundos,
                       bpm=excluded.bpm,
                       instrumentos=excluded.instrumentos,
                       partitura_path=excluded.partitura_path,
                       source_artist_id=excluded.source_artist_id,
                       produtor_id=excluded.produtor_id""",
                (
                    id, caminho_audio, genero_origem, duracao_segundos, bpm,
                    instrumentos_json, partitura_path, source_artist_id, produtor_id,
                ),
            )
        return id

    def get_faixa(self, id: str) -> "Faixa | None":
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM faixas WHERE id = ?", (id,)).fetchone()
        if row is None:
            return None
        data = dict(row)
        data["instrumentos"] = json.loads(data["instrumentos"]) if data["instrumentos"] else []
        return Faixa(**data)

    def list_faixas(
        self, produtor_id: int | None = None, genero_origem: str | None = None
    ) -> list[Faixa]:
        query = "SELECT * FROM faixas WHERE 1=1"
        params: list = []
        if produtor_id is not None:
            query += " AND produtor_id = ?"
            params.append(produtor_id)
        if genero_origem:
            query += " AND genero_origem = ?"
            params.append(genero_origem)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        resultado = []
        for r in rows:
            data = dict(r)
            data["instrumentos"] = json.loads(data["instrumentos"]) if data["instrumentos"] else []
            resultado.append(Faixa(**data))
        return resultado

    # ---- vozes detectadas ----

    def add_voz_detectada(
        self,
        faixa_id: str,
        segmento_indice: int | None = None,
        perfil_vocal: str | None = None,
        genero_vocal: str | None = None,
        confianca: float | None = None,
    ) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                """INSERT INTO vozes_detectadas
                   (faixa_id, segmento_indice, perfil_vocal, genero_vocal, confianca)
                   VALUES (?, ?, ?, ?, ?)
                   RETURNING id""",
                (faixa_id, segmento_indice, perfil_vocal, genero_vocal, confianca),
            )
            return cur.fetchone()["id"]

    def list_vozes_for_faixa(self, faixa_id: str) -> list[VozDetectada]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM vozes_detectadas WHERE faixa_id = ? ORDER BY segmento_indice",
                (faixa_id,),
            ).fetchall()
        return [VozDetectada(**dict(r)) for r in rows]
