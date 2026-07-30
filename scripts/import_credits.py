import sqlite3

credits = {
    "track": "Olvidé Olvidarte",
    "artist": "Alfredo Escudero, Leonidas Moreno y Los Montañeros",
    "composer": "Edward Cedeño",
    "album": "LO BONITO DE AMAR",
    "year": "2018",
    "label": "J&C ENTERTAINMENT S.A.",
    "studio": "A&L STUDIO",
    "engineer": "Alberto Ruiz & Rodrigo Barría",
    "manager": "Joel Escudero",
    "instagram": "@alfredoescuderooficial"
}

conn = sqlite3.connect("outputs/catalogo_validado.sqlite")
cursor = conn.cursor()
cursor.execute("""
    UPDATE tracks SET
        matched_artist = ?,
        matched_title = ?,
        release_title = ?,
        release_date = ?,
        notes = ?
    WHERE detected_title LIKE ?
""", (
    credits["artist"],
    credits["track"],
    credits["album"],
    credits["year"],
    f"Compositor: {credits['composer']}, Gravadora: {credits['label']}",
    f"%{credits['track']}%"
))
conn.commit()
conn.close()
print("✅ Créditos importados para Olvidé Olvidarte")
