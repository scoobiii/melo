import csv
import sqlite3
from pathlib import Path

csv_path = "data/creditos.csv"
db_path = "outputs/catalogo_validado.sqlite"

if not Path(csv_path).exists():
    print(f"❌ CSV não encontrado: {csv_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

with open(csv_path, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        track = row["track"]
        cursor.execute("""
            UPDATE tracks SET
                matched_artist = ?,
                matched_title = ?,
                release_title = ?,
                release_date = ?,
                notes = ?
            WHERE detected_title LIKE ?
        """, (
            row["artist"],
            track,
            row["album"],
            row["year"],
            f"Compositor: {row['composer']}, Gravadora: {row['label']}, Estúdio: {row['studio']}, Engenheiro: {row['engineer']}, Manager: {row['manager']}, Instagram: {row['instagram']}",
            f"%{track}%"
        ))
        print(f"✅ {track} atualizado")

conn.commit()
conn.close()
print("✅ Importação concluída.")
