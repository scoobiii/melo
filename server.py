#!/usr/bin/env python3
from flask import Flask, jsonify, send_from_directory
import sqlite3
from pathlib import Path

app = Flask(__name__, static_folder="static")
DB_PATH = "outputs/catalogo_validado.sqlite"

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
            "start": row[1] or 0,
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
