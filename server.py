#!/usr/bin/env python3
from flask import Flask, jsonify, send_from_directory
import sqlite3
from pathlib import Path

app = Flask(__name__, static_folder="static")
DB_PATH = "outputs/catalogo_validado.sqlite"

def parse_time(timestr):
    """Converte HH:MM:SS para segundos."""
    if not timestr:
        return 0.0
    parts = str(timestr).split(':')
    if len(parts) == 3:
        return float(int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2]))
    elif len(parts) == 2:
        return float(int(parts[0]) * 60 + int(parts[1]))
    else:
        return float(parts[0])

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/api/tracks")
def get_tracks():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT segment, start_time, matched_artist, matched_title, confidence, status, notes
        FROM tracks
        ORDER BY segment
    """)
    rows = cursor.fetchall()
    conn.close()
    tracks = [
        {
            "segment": row[0],
            "start": parse_time(row[1]),
            "artist": row[2] or "",
            "title": row[3] or "",
            "confidence": row[4],
            "status": row[5],
            "notes": row[6]
        }
        for row in rows
    ]
    return jsonify(tracks)

@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "db": str(DB_PATH)})

@app.route("/api/mix")
def get_mix():
    conn = sqlite3.connect("melo_catalog.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, instagram, soundcloud, download_link, call_to_action FROM mixes WHERE id = 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        return jsonify({
            "id": row[0],
            "instagram": row[1] or "",
            "soundcloud": row[2] or "",
            "download_link": row[3] or "",
            "call_to_action": row[4] or ""
        })
    return jsonify({"error": "Mix not found"}), 404
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
