#!/usr/bin/env python3
"""
Atualiza o JSON de transcrição com metadados extraídos do YouTube.
Uso: python scripts/update_from_youtube.py --json melo-transcription-*.json --url https://youtu.be/XYNx6SK-9U8 --segment 0
"""
import json
import sys
import subprocess
import re
from pathlib import Path
from urllib.parse import urlparse, parse_qs

def get_youtube_metadata(url):
    """Extrai título e canal do YouTube usando yt-dlp (sem baixar)."""
    cmd = [
        "yt-dlp",
        "--skip-download",
        "--print", "%(title)s|%(channel)s",
        url
    ]
    try:
        output = subprocess.check_output(cmd, text=True).strip()
        if not output:
            return None, None
        parts = output.split("|", 1)
        title = parts[0].strip() if len(parts) > 0 else None
        channel = parts[1].strip() if len(parts) > 1 else None
        return title, channel
    except Exception as e:
        print(f"❌ Erro ao obter metadados: {e}")
        return None, None

def extract_artist_title(title):
    """Tenta extrair artista e título do título do vídeo."""
    # Remove parênteses, colchetes, etc.
    clean = re.sub(r"[\(\[].*?[\)\]]", "", title).strip()
    # Padrões comuns: "Artista - Música", "Artista – Música", "Artista — Música"
    for sep in [" - ", " – ", " — "]:
        if sep in clean:
            artist, song = clean.split(sep, 1)
            return artist.strip(), song.strip()
    return "", clean

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", required=True, help="Caminho do JSON")
    parser.add_argument("--url", required=True, help="URL do YouTube")
    parser.add_argument("--segment", type=int, help="Índice do segmento (0-based) a atualizar")
    parser.add_argument("--dry-run", action="store_true", help="Mostra o que seria feito")
    args = parser.parse_args()

    if not Path(args.json).exists():
        print(f"❌ JSON não encontrado: {args.json}")
        sys.exit(1)

    with open(args.json, "r", encoding="utf-8") as f:
        data = json.load(f)

    segments = data.get("segments", [])
    if not segments:
        print("❌ Nenhum segmento encontrado.")
        sys.exit(1)

    # Obter metadados do YouTube
    title, channel = get_youtube_metadata(args.url)
    if not title:
        print("❌ Não foi possível obter o título do vídeo.")
        sys.exit(1)

    artist, song = extract_artist_title(title)
    if not artist and not song:
        print("⚠️ Não foi possível extrair artista/título do título do vídeo.")
        artist = channel or "Artista Desconhecido"
        song = title

    print(f"📺 Vídeo: {title}")
    print(f"   Canal: {channel}")
    print(f"   Artista: {artist}")
    print(f"   Música: {song}")

    # Determinar qual segmento atualizar
    if args.segment is not None:
        idx = args.segment
        if idx < 0 or idx >= len(segments):
            print(f"❌ Índice {idx} inválido (0-{len(segments)-1})")
            sys.exit(1)
        indices = [idx]
    else:
        # Fallback: procurar por similaridade com a letra (usando o texto do segmento)
        # Por simplicidade, vamos pedir para o usuário escolher
        print("\n🔍 Segmentos disponíveis:")
        for i, seg in enumerate(segments):
            text = seg.get("text", "")[:50].replace("\n", " ")
            print(f"  [{i}] {seg.get('artist', '?')} - {text}...")
        try:
            idx = int(input("\nDigite o índice do segmento a atualizar: "))
        except ValueError:
            print("❌ Índice inválido.")
            sys.exit(1)
        indices = [idx]

    if args.dry_run:
        for i in indices:
            print(f"\n🔎 DRY-RUN: Segmento {i} seria atualizado para:")
            print(f"   Artista: {artist}")
            print(f"   Título: {song}")
        return

    # Atualizar
    for i in indices:
        seg = segments[i]
        old = seg.get("artist", "")
        seg["artist"] = f"{artist} - {song}"
        # Opcional: adicionar metadados extras
        seg["youtube_channel"] = channel
        seg["youtube_url"] = args.url
        print(f"✅ Segmento {i} atualizado:")
        print(f"   Antes: {old}")
        print(f"   Depois: {artist} - {song}")

    # Salvar backup e atualizar
    backup = args.json + ".bak"
    Path(args.json).rename(backup)
    with open(args.json, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\n✅ JSON atualizado. Backup salvo em {backup}")

if __name__ == "__main__":
    main()
