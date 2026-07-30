import sqlite3

conn = sqlite3.connect("melo_catalog.db")
conn.row_factory = sqlite3.Row

def titulo(txt):
    print(f"\n{'='*70}\n{txt}\n{'='*70}")

titulo("TABELAS EXISTENTES")
for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
    count = conn.execute(f"SELECT COUNT(*) as n FROM {r['name']}").fetchone()["n"]
    print(f"  {r['name']}: {count} linhas")

titulo("SOURCE_ARTISTS (todos)")
for r in conn.execute("SELECT * FROM source_artists ORDER BY id"):
    print(dict(r))

titulo("DESTINATION_ARTISTS (todos)")
try:
    for r in conn.execute("SELECT * FROM destination_artists ORDER BY id"):
        print(dict(r))
except sqlite3.OperationalError as e:
    print(f"  (erro: {e})")

titulo("PRODUTORES (todos)")
try:
    for r in conn.execute("SELECT * FROM produtores ORDER BY id"):
        print(dict(r))
except sqlite3.OperationalError as e:
    print(f"  (erro: {e})")

titulo("FAIXAS (todas)")
try:
    for r in conn.execute("SELECT * FROM faixas ORDER BY id"):
        print(dict(r))
except sqlite3.OperationalError as e:
    print(f"  (erro: {e})")

titulo("MIXES (todos)")
for r in conn.execute("SELECT * FROM mixes ORDER BY id"):
    print(dict(r))

titulo("MIX_TRACKS com JOIN em source_artists (tracklist completo, todos os mixes)")
query = """
SELECT
    m.dj_nome,
    m.arquivo_path AS mix_origem,
    mt.mix_id,
    mt.track_indice,
    mt.inicio_segundos,
    mt.fim_segundos,
    mt.status_identificacao,
    mt.titulo_identificado,
    sa.nome AS artista,
    mt.fingerprint_servico,
    mt.fingerprint_confianca
FROM mix_tracks mt
JOIN mixes m ON mt.mix_id = m.id
LEFT JOIN source_artists sa ON mt.source_artist_id = sa.id
ORDER BY mt.mix_id, mt.track_indice
"""
for r in conn.execute(query):
    d = dict(r)
    m1, s1 = int(d["inicio_segundos"] // 60), int(d["inicio_segundos"] % 60)
    artista = d["artista"] or "(sem artista identificado)"
    print(f"  mix={d['mix_id']} [{d['track_indice']:2d}] {m1}m{s1:02d}s | "
          f"{artista} — {d['titulo_identificado']} "
          f"(status={d['status_identificacao']}, fonte={d['fingerprint_servico']}, "
          f"confianca={d['fingerprint_confianca']})")

titulo("RESUMO")
n_artistas = conn.execute("SELECT COUNT(*) as n FROM source_artists").fetchone()["n"]
n_mixes = conn.execute("SELECT COUNT(*) as n FROM mixes").fetchone()["n"]
n_tracks = conn.execute("SELECT COUNT(*) as n FROM mix_tracks").fetchone()["n"]
n_com_artista = conn.execute(
    "SELECT COUNT(*) as n FROM mix_tracks WHERE source_artist_id IS NOT NULL"
).fetchone()["n"]
print(f"  {n_artistas} artistas cadastrados (source_artists)")
print(f"  {n_mixes} mixes cadastrados")
print(f"  {n_tracks} trechos de mix_tracks, {n_com_artista} com artista vinculado")

conn.close()
