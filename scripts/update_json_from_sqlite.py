import json
import sqlite3

conn = sqlite3.connect("outputs/catalogo_validado.sqlite")
cursor = conn.cursor()
cursor.execute("SELECT segment, matched_artist, matched_title FROM tracks ORDER BY segment")
rows = cursor.fetchall()
conn.close()

with open("melo-transcription-1785367803211.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for seg, artist, title in rows:
    idx = seg - 1
    if idx < len(data["segments"]):
        if artist and title:
            data["segments"][idx]["artist"] = f"{artist} - {title}"
        elif artist:
            data["segments"][idx]["artist"] = artist
        elif title:
            data["segments"][idx]["artist"] = title

with open("melo-transcription-1785367803211.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("✅ JSON atualizado com os dados do SQLite.")
