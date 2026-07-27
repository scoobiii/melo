#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# Arquivo: scripts/add_vocal_profiles.py
# Responsabilidade:
#   Aplica ao packages/catalog/store.py real: tabelas vocal_profiles e
#   digital_twins, coluna vocal_profile_id em destination_artists, e os
#   métodos de CRUD/busca correspondentes.
#
# Diferença deliberada em relação a scripts/add_industry_ids.sh (que já
# causou um bug real de duplicação nesta sessão — ver HANDOFF.md, lição #9):
#   1. Idempotência checada pelo RESULTADO (a classe VocalProfile já existe
#      no arquivo? o método _apply_vocal_profile_migrations já existe?),
#      não pela âncora de inserção — que continua presente mesmo depois de
#      já aplicado, e por isso não serve como checagem de "já rodou".
#   2. TODAS as âncoras são validadas ANTES de qualquer escrita. Se uma só
#      faltar, aborta sem tocar no arquivo — nunca aplica só metade.
#   3. NÃO commita nem faz push. Para no teste, imprime os próximos passos.
# -----------------------------------------------------------------------------
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STORE = ROOT / "packages" / "catalog" / "store.py"


def abortar(msg: str):
    print(f"ERRO: {msg}")
    print("Abortando SEM alterar nenhum arquivo.")
    sys.exit(1)


def main():
    if not STORE.exists():
        abortar(f"{STORE} não encontrado.")

    src = STORE.read_text(encoding="utf-8")

    # --- Checagem de idempotência pelo RESULTADO, não pela âncora ---
    if "class VocalProfile" in src or "_apply_vocal_profile_migrations" in src:
        print("==> Migração de vocal_profiles/digital_twins já aplicada "
              "(class VocalProfile ou _apply_vocal_profile_migrations "
              "já existe no arquivo). Nada a fazer.")
        sys.exit(0)

    # --- Definição de todas as edições, com suas âncoras ---
    edicoes = []

    # 1) Novas tabelas no final do _SCHEMA
    ancora_schema = '''CREATE TABLE IF NOT EXISTS mix_tracks (
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
"""'''
    novo_schema = '''CREATE TABLE IF NOT EXISTS mix_tracks (
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
"""'''
    edicoes.append(("schema (novas tabelas)", ancora_schema, novo_schema))

    # 2) _init_schema chama a nova migração
    ancora_init = '''    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(_SCHEMA)
        self._apply_industry_id_migrations()'''
    novo_init = '''    def _init_schema(self) -> None:
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
                )'''
    edicoes.append(("_init_schema + nova migração", ancora_init, novo_init))

    # 3) Dataclasses novas, ao lado de DestinationArtist
    ancora_dataclass = '''@dataclass(frozen=True)
class SegmentMapping:'''
    novo_dataclass = '''@dataclass(frozen=True)
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
class SegmentMapping:'''
    edicoes.append(("dataclasses novas", ancora_dataclass, novo_dataclass))

    # 4) Métodos novos, ao final da classe (depois de list_tracks_for_mix)
    ancora_metodos = '''    def list_tracks_for_mix(
        self, mix_id: int, apenas_identificadas: bool = False
    ) -> list[MixTrack]:
        query = "SELECT * FROM mix_tracks WHERE mix_id = ?"
        params: list = [mix_id]
        if apenas_identificadas:
            query += " AND status_identificacao = 'identificado'"
        query += " ORDER BY track_indice"
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [MixTrack(**dict(r)) for r in rows]'''
    novo_metodos = ancora_metodos + '''

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
        ]'''
    edicoes.append(("métodos novos", ancora_metodos, novo_metodos))

    # --- Validação TOTAL antes de qualquer escrita (tudo ou nada) ---
    for nome, ancora, _ in edicoes:
        if ancora not in src:
            abortar(
                f"âncora de '{nome}' não encontrada — o arquivo pode ter "
                f"mudado de estrutura desde que este script foi escrito. "
                f"Nenhuma edição foi aplicada."
            )
    print("==> Todas as 4 âncoras encontradas. Aplicando edições...")

    novo_src = src
    for nome, ancora, novo in edicoes:
        if novo_src.count(ancora) != 1:
            abortar(
                f"âncora de '{nome}' aparece {novo_src.count(ancora)}x "
                f"(esperado 1x) — ambíguo demais pra aplicar com segurança."
            )
        novo_src = novo_src.replace(ancora, novo, 1)
        print(f"    aplicado: {nome}")

    STORE.write_text(novo_src, encoding="utf-8")
    print(f"==> {STORE} atualizado.")

    # --- Teste imediato ---
    print("\n==> Testando em banco novo...")
    teste = subprocess.run(
        [sys.executable, "-c",
         "from packages.catalog.store import CatalogStore\n"
         "c = CatalogStore(':memory:')\n"
         "c.add_source_artist('Teste', 'tipico_panameno')\n"
         "vp = c.add_vocal_profile('medio', 'rouco', 'profissional')\n"
         "print('OK: schema novo funciona, vocal_profile id=', vp)"],
        cwd=ROOT, capture_output=True, text=True,
    )
    print(teste.stdout)
    if teste.returncode != 0:
        print("ERRO no teste rápido:")
        print(teste.stderr)
        print("\nO arquivo FOI alterado, mas o teste falhou. Revise manualmente:")
        print(f"  git diff -- {STORE.relative_to(ROOT)}")
        sys.exit(1)

    print("==> Rodando suíte completa...")
    suite = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-q"], cwd=ROOT
    )
    if suite.returncode != 0:
        print("\nSuíte falhou. Revise antes de commitar:")
        print(f"  git diff -- {STORE.relative_to(ROOT)}")
        sys.exit(1)

    print("\n==================================================================")
    print("==> Tudo passou. Este script NÃO commita nem publica — revise e:")
    print("==================================================================")
    print(f"  git diff -- {STORE.relative_to(ROOT)}")
    print(f'  git add {STORE.relative_to(ROOT)}')
    print('  git commit -m "feat(catalog): vocal_profiles + digital_twins '
          '(perfis vocais estruturados e gêmeos digitais licenciados)"')
    print("  git push origin main")


if __name__ == "__main__":
    main()
