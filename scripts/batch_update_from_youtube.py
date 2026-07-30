#!/usr/bin/env python3
"""
Varre todos os segmentos do JSON, busca no YouTube, e atualiza artistas/títulos.
Usa yt-dlp (sem API) para pesquisa e extração de metadados.
Uso: python scripts/batch_update_from_youtube.py --json melo-transcription-*.json --dry-run
"""
import json
import sys
import subprocess
import re
import time
from pathlib import Path
from urllib.parse import urlparse, parse_qs

def search_youtube(query, max_results=1):
    """Pesquisa no YouTube e retorna títulos, canais e URLs."""
    cmd = [
        "yt-dlp",
        f"ytsearch{max_results}:{query}",
        "--skip-download",
        "--print", "%(title)s|%(channel)s|%(url)s"
    ]
    try:
        output = subprocess.check_output(cmd, text=True).strip()
        if not output:
            return []
        results = []
        for line in output.split("\n"):
            if not line.strip():
                continue
            parts = line.split("|", 2)
            if len(parts) >= 3:
                title, channel, url = parts[0], parts[1], parts[2]
                results.append({"title": title, "channel": channel, "url": url})
        return results
    except Exception as e:
        print(f"   ⚠️ Erro na busca: {e}")
        return []

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

def normalize_title(title):
    """Normaliza título para comparação (remove acentos, minúsculas)."""
    import unicodedata
    title = unicodedata.normalize("NFD", title)
    title = re.sub(r"[\u0300-\u036f]", "", title)
    return title.lower().strip()

def is_similar(title1, title2, threshold=0.7):
    """Verifica similaridade entre títulos (usando simples razão de caracteres)."""
    from difflib import SequenceMatcher
    return SequenceMatcher(None, normalize_title(title1), normalize_title(title2)).ratio() >= threshold

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", required=True, help="Caminho do JSON")
    parser.add_argument("--dry-run", action="store_true", help="Mostra o que seria feito, sem salvar")
    parser.add_argument("--threshold", type=float, default=0.7, help="Limiar de similaridade para aceitar resultado (0-1)")
    args = parser.parse_args()

    json_path = Path(args.json)
    if not json_path.exists():
        print(f"❌ JSON não encontrado: {json_path}")
        sys.exit(1)

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    segments = data.get("segments", [])
    print(f"🔍 Processando {len(segments)} segmentos...\n")

    updates = []
    for idx, seg in enumerate(segments):
        current_artist = seg.get("artist", "")
        # Tentar extrair artista e título atuais (se no formato "Artista - Título")
        if " - " in current_artist:
            old_artist, old_title = current_artist.split(" - ", 1)
        else:
            old_artist = ""
            old_title = current_artist

        # Se não tiver título, usar o texto da letra (primeira frase) como fallback
        if not old_title:
            text = seg.get("text", "")
            old_title = text[:50].strip().split()[0] if text else ""

        # Montar query: usar artista + título se disponível, senão título
        query = f"{old_artist} {old_title} cancion oficial" if old_artist else f"{old_title} cancion oficial"
        print(f"[{idx+1:02d}/{len(segments):02d}] {query}")

        results = search_youtube(query, max_results=1)
        if not results:
            print("   ❌ Nenhum resultado encontrado.")
            continue

        best = results[0]
        title = best["title"]
        channel = best["channel"]
        url = best["url"]
        new_artist, new_title = extract_artist_title(title)

        # Se não conseguiu extrair, usa o canal como artista
        if not new_artist and not new_title:
            new_artist = channel or "Artista Desconhecido"
            new_title = title

        # Verificar similaridade para evitar falsos positivos
        if old_title and new_title:
            if not is_similar(old_title, new_title, args.threshold):
                print(f"   ⚠️ Baixa similaridade: '{old_title}' vs '{new_title}' (pular)")
                continue

        # Se já está correto, pular
        new_entry = f"{new_artist} - {new_title}"
        if new_entry == current_artist:
            print(f"   ✅ Já está correto: {new_entry}")
            continue

        # Registrar mudança
        updates.append({
            "index": idx,
            "old": current_artist,
            "new": new_entry,
            "url": url,
            "channel": channel
        })
        print(f"   🔄 {current_artist} → {new_entry}")

        time.sleep(0.5)  # evitar rate limit

    if args.dry_run:
        print("\n📋 DRY-RUN: mudanças propostas:")
        for u in updates:
            print(f"  [{u['index']}] {u['old']} → {u['new']} (via {u['url']})")
        print("\n✅ Nenhuma alteração salva. Remova --dry-run para aplicar.")
        return

    # Aplicar mudanças
    if not updates:
        print("\n✅ Nenhuma atualização necessária.")
        return

    print("\n📝 Aplicando mudanças...")
    for u in updates:
        segments[u["index"]]["artist"] = u["new"]
        # Adicionar metadados extras
        segments[u["index"]]["youtube_url"] = u["url"]
        segments[u["index"]]["youtube_channel"] = u["channel"]

    # Salvar backup
    backup_path = json_path.with_suffix(".json.bak")
    json_path.rename(backup_path)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\n✅ JSON atualizado. Backup salvo em {backup_path}")

if __name__ == "__main__":
    main()
