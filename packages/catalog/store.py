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
- produtores / faixas / vozes_detectadas: catálogo de faixas já
  processadas, com metadados de instrumentos, partitura e voz detectada
- mixes / mix_tracks: um arquivo de DJ contém N faixas de N artistas
  diferentes; royalty só faz sentido calculado por mix_track identificada,
  nunca pelo mix inteiro como se fosse uma obra única

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

-- Um mix de DJ é um arquivo contendo N faixas de N artistas/gravadoras
-- diferentes. Royalty só faz sentido calculado por mix_track identificada,
-- nunca pelo mix inteiro como se fosse uma obra única.
CREATE TABLE IF NOT EXISTS mixes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dj_nome TEXT NOT NULL,
    arquivo_path TEXT NOT NULL UNIQUE,
    duracao_segundos REAL,
    -- plataformas onde o DJ declara distribuir/monetizar este mix.
    -- Preenchido por DECLARAÇÃO do próprio DJ no cadastro, nunca por
    -- coleta automatizada de dados de terceiro.
    plataformas_distribuicao TEXT  -- JSON list como texto: ["youtube", "soundcloud"]
);

CREATE TABLE IF NOT EXISTS mix_tracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mix_id INTEGER NOT NULL REFERENCES mixes(id),
    track_indice INTEGER NOT NULL,
    inicio_segundos REAL NOT NULL,
    fim_segundos REAL,
    status_identificacao TEXT NOT NULL DEFAULT 'nao_identificado',
        -- 'nao_identificado' | 'identificado' | 'identificacao_incerta'
    titulo_identificado TEXT,
    source_artist_id INTEGER REFERENCES source_artists(id),
    fingerprint_servico TEXT,
    fingerprint_confianca REAL,
    UNIQUE(mix_id, track_indice)
);

CREATE TABLE IF NOT EXISTS vocal_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tessitura TEXT NOT NULL,
    textura TEXT NOT NULL,
    nivel TEXT NOT NULL,
    notas TEXT,
    UNIQUE(tessitura, textura, nivel)
);

CREATE TABLE IF NOT EXISTS digital_twins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    artist_type TEXT NOT NULL,
    artist_id INTEGER NOT NULL,
    status_consentimento TEXT NOT NULL DEFAULT 'nao_licenciado',
    data_licenca TEXT,
    modelo_referencia TEXT,
    ativo INTEGER NOT NULL DEFAULT 0,
    UNIQUE(artist_type, artist_id)
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
    isni: Optional[str] = None
    ipi_number: Optional[str] = None


@dataclass(frozen=True)
class DestinationArtist:
    id: int
    nome: str
    genero_destino: str
    regiao: Optional[str]
    perfil_vocal: Optional[str]
    disponivel: bool


@dataclass(frozen=True)
class VocalProfile:
    id: int
    tessitura: str
    textura: str
    nivel: str
    notas: Optional[str]


@dataclass(frozen=True)
class DigitalTwin:
    id: int
    artist_type: str
    artist_id: int
    status_consentimento: str
    data_licenca: Optional[str]
    modelo_referencia: Optional[str]
    ativo: bool


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
    ipi_number: Optional[str] = None
    ddex_party_id: Optional[str] = None


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
    isrc: Optional[str] = None
    iswc: Optional[str] = None
    upc: Optional[str] = None


@dataclass(frozen=True)
class VozDetectada:
    id: int
    faixa_id: str
    segmento_indice: Optional[int]
    perfil_vocal: Optional[str]
    genero_vocal: Optional[str]
    confianca: Optional[float]


@dataclass(frozen=True)
class Mix:
    id: int
    dj_nome: str
    arquivo_path: str
    duracao_segundos: Optional[float]
    plataformas_distribuicao: Optional[str]  # JSON como texto


@dataclass(frozen=True)
class MixTrack:
    id: int
    mix_id: int
    track_indice: int
    inicio_segundos: float
    fim_segundos: Optional[float]
    status_identificacao: str
    titulo_identificado: Optional[str]
    source_artist_id: Optional[int]
    fingerprint_servico: Optional[str]
    fingerprint_confianca: Optional[float]


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
        self._apply_industry_id_migrations()
        self._apply_vocal_profile_migrations()

    def _apply_vocal_profile_migrations(self) -> None:
        """Adiciona vocal_profile_id a destination_artists.

        Idempotência correta (lição #9 do HANDOFF): checa se a coluna já
        existe via PRAGMA table_info (o resultado real no banco), não via
        âncora de texto no arquivo fonte.
        """
        with self._connect() as conn:
            info = conn.execute("PRAGMA table_info(destination_artists)").fetchall()
            colunas = {row["name"] for row in info}
            if "vocal_profile_id" not in colunas:
                conn.execute(
                    "ALTER TABLE destination_artists ADD COLUMN vocal_profile_id "
                    "INTEGER REFERENCES vocal_profiles(id)"
                )

    def _apply_industry_id_migrations(self) -> None:
        """Adiciona colunas de identificadores padrão de indústria
        (ISRC/ISWC/ISNI/IPI/UPC/DDEX) via ALTER TABLE ADD COLUMN.

        Idempotente: cada ALTER roda dentro de try/except OperationalError
        (SQLite não tem 'ADD COLUMN IF NOT EXISTS'). Se a coluna já existe
        de uma migração anterior, ignora silenciosamente.

        Por que isso importa: sem ISRC/ISWC não há como casar
        automaticamente uma faixa do catálogo com um registro real do
        ECAD — o schema atual dedup por (nome, faixa_original), que é
        string livre, não código padronizado. Ver docs/SWOT.md, seção
        'MELO vs. bases de indústria'.
        """
        migrations = [
            ("source_artists", "isni", "TEXT"),
            ("source_artists", "ipi_number", "TEXT"),
            ("destination_artists", "isni", "TEXT"),
            ("faixas", "isrc", "TEXT"),
            ("faixas", "iswc", "TEXT"),
            ("faixas", "upc", "TEXT"),
            ("produtores", "ipi_number", "TEXT"),
            ("produtores", "ddex_party_id", "TEXT"),
        ]
        with self._connect() as conn:
            for table, column, coltype in migrations:
                try:
                    conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {coltype}")
                except sqlite3.OperationalError as exc:
                    if "duplicate column name" not in str(exc):
                        raise

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

    # ---- mixes (arquivos de DJ com múltiplas faixas) ----

    def add_mix(
        self,
        dj_nome: str,
        arquivo_path: str,
        duracao_segundos: float | None = None,
        plataformas_distribuicao: list[str] | None = None,
    ) -> int:
        plataformas_json = (
            json.dumps(plataformas_distribuicao) if plataformas_distribuicao else None
        )
        with self._connect() as conn:
            cur = conn.execute(
                """INSERT INTO mixes
                   (dj_nome, arquivo_path, duracao_segundos, plataformas_distribuicao)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(arquivo_path) DO UPDATE SET
                       dj_nome=excluded.dj_nome,
                       duracao_segundos=excluded.duracao_segundos,
                       plataformas_distribuicao=excluded.plataformas_distribuicao
                   RETURNING id""",
                (dj_nome, arquivo_path, duracao_segundos, plataformas_json),
            )
            return cur.fetchone()["id"]

    def get_mix_by_path(self, arquivo_path: str) -> Optional[Mix]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM mixes WHERE arquivo_path = ?", (arquivo_path,)
            ).fetchone()
        return Mix(**dict(row)) if row else None

    def add_mix_track(
        self,
        mix_id: int,
        track_indice: int,
        inicio_segundos: float,
        fim_segundos: float | None = None,
    ) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                """INSERT INTO mix_tracks
                   (mix_id, track_indice, inicio_segundos, fim_segundos)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(mix_id, track_indice) DO UPDATE SET
                       inicio_segundos=excluded.inicio_segundos,
                       fim_segundos=excluded.fim_segundos
                   RETURNING id""",
                (mix_id, track_indice, inicio_segundos, fim_segundos),
            )
            return cur.fetchone()["id"]

    def identify_mix_track(
        self,
        mix_track_id: int,
        titulo_identificado: str,
        fingerprint_servico: str,
        fingerprint_confianca: float,
        source_artist_id: int | None = None,
        confianca_minima_aceitavel: float = 0.7,
    ) -> None:
        """Registra o resultado de uma identificação por fingerprint.

        Se a confiança vier abaixo de `confianca_minima_aceitavel`, marca
        como 'identificacao_incerta' em vez de 'identificado' — isso evita
        que uma identificação de baixa confiança entre no cálculo de
        royalty como se fosse certeza.
        """
        if not (0.0 <= fingerprint_confianca <= 1.0):
            raise ValueError(
                f"fingerprint_confianca deve estar entre 0 e 1, "
                f"recebido: {fingerprint_confianca}"
            )
        status = (
            "identificado"
            if fingerprint_confianca >= confianca_minima_aceitavel
            else "identificacao_incerta"
        )
        with self._connect() as conn:
            conn.execute(
                """UPDATE mix_tracks SET
                       status_identificacao = ?,
                       titulo_identificado = ?,
                       source_artist_id = ?,
                       fingerprint_servico = ?,
                       fingerprint_confianca = ?
                   WHERE id = ?""",
                (
                    status,
                    titulo_identificado,
                    source_artist_id,
                    fingerprint_servico,
                    fingerprint_confianca,
                    mix_track_id,
                ),
            )

    def list_tracks_for_mix(
        self, mix_id: int, apenas_identificadas: bool = False
    ) -> list[MixTrack]:
        query = "SELECT * FROM mix_tracks WHERE mix_id = ?"
        params: list = [mix_id]
        if apenas_identificadas:
            query += " AND status_identificacao = 'identificado'"
        query += " ORDER BY track_indice"
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [MixTrack(**dict(r)) for r in rows]

    # ---- vocal profiles / gêmeos digitais ----

    def add_vocal_profile(
        self, tessitura: str, textura: str, nivel: str, notas: str | None = None
    ) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                """INSERT INTO vocal_profiles (tessitura, textura, nivel, notas)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(tessitura, textura, nivel) DO UPDATE SET
                       notas=excluded.notas
                   RETURNING id""",
                (tessitura, textura, nivel, notas),
            )
            return cur.fetchone()["id"]

    def find_destination_artists_by_vocal_profile(
        self, tessitura: str, textura: str, nivel: str | None = None,
        apenas_disponiveis: bool = True,
    ) -> list[DestinationArtist]:
        """Rankeia artistas de destino por proximidade de perfil vocal.

        Match exato em tessitura+textura primeiro; nivel é filtro opcional.
        """
        query = """
            SELECT da.* FROM destination_artists da
            JOIN vocal_profiles vp ON da.vocal_profile_id = vp.id
            WHERE vp.tessitura = ? AND vp.textura = ?
        """
        params: list = [tessitura, textura]
        if nivel:
            query += " AND vp.nivel = ?"
            params.append(nivel)
        if apenas_disponiveis:
            query += " AND da.disponivel = 1"
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [
            DestinationArtist(
                id=r["id"], nome=r["nome"], genero_destino=r["genero_destino"],
                regiao=r["regiao"], perfil_vocal=r["perfil_vocal"],
                disponivel=bool(r["disponivel"]),
            )
            for r in rows
        ]

    def add_digital_twin(
        self,
        artist_type: str,
        artist_id: int,
        status_consentimento: str = "nao_licenciado",
        data_licenca: str | None = None,
        modelo_referencia: str | None = None,
        ativo: bool = False,
    ) -> int:
        if artist_type not in ("source", "destination"):
            raise ValueError(
                f"artist_type deve ser 'source' ou 'destination', recebido: {artist_type!r}"
            )
        # Trava de segurança: nunca marcar ativo=True sem consentimento
        # explícito registrado.
        if ativo and status_consentimento != "licenciado":
            raise ValueError(
                "Não é possível ativar um gêmeo digital sem "
                "status_consentimento='licenciado'."
            )
        with self._connect() as conn:
            cur = conn.execute(
                """INSERT INTO digital_twins
                   (artist_type, artist_id, status_consentimento, data_licenca,
                    modelo_referencia, ativo)
                   VALUES (?, ?, ?, ?, ?, ?)
                   ON CONFLICT(artist_type, artist_id) DO UPDATE SET
                       status_consentimento=excluded.status_consentimento,
                       data_licenca=excluded.data_licenca,
                       modelo_referencia=excluded.modelo_referencia,
                       ativo=excluded.ativo
                   RETURNING id""",
                (artist_type, artist_id, status_consentimento, data_licenca,
                 modelo_referencia, int(ativo)),
            )
            return cur.fetchone()["id"]

    def list_digital_twins(self, apenas_ativos: bool = True) -> list[DigitalTwin]:
        query = "SELECT * FROM digital_twins"
        if apenas_ativos:
            query += " WHERE ativo = 1"
        with self._connect() as conn:
            rows = conn.execute(query).fetchall()
        return [
            DigitalTwin(
                id=r["id"], artist_type=r["artist_type"], artist_id=r["artist_id"],
                status_consentimento=r["status_consentimento"],
                data_licenca=r["data_licenca"], modelo_referencia=r["modelo_referencia"],
                ativo=bool(r["ativo"]),
            )
            for r in rows
        ]
