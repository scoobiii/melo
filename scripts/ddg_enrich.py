#!/usr/bin/env python3
"""
Enriquece o catálogo musical usando DuckDuckGo (sem API key).
Uso: python scripts/ddg_enrich.py --json melo-transcription-*.json --dry-run
"""
import json
import sys
import re
import time
from pathlib import Path
from difflib import SequenceMatcher

try:
    from ddgs import DDGS
except ImportError:
    print("❌ Instale o pacote: pip install ddgs")
    sys.exit(1)

def normalize(text):
    """Remove acentos, pontuação e normaliza para comparação."""
    import unicodedata
    text = unicodedata.normalize("NFD", text)
    text = re.sub(r"[\u0300-\u036f]", "", text)
    text = re.sub(r"[^\w\s]", "", text)
    return text.lower().strip()

def similarity(a, b):
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()

def search_ddg(query, max_results=3):
    """Busca no DuckDuckGo e retorna resultados com título, URL e snippet."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            return results
    except Exception as e:
        print(f"   ⚠️ Erro na busca: {e}")
        return []

def extract_artist_title(text):
    """Tenta extrair artista e título de um texto."""
    # Remove parênteses/colchetes e marcadores comuns
    clean = re.sub(r"[\(\[].*?[\)\]]", "", text)
    clean = re.sub(r"(Video Oficial|Official Video|Lyric|Audio|Remix|Cover|En Vivo|Live)", "", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\s+", " ", clean).strip()

    # Tenta separar por " - ", " – ", " — "
    for sep in [" - ", " – ", " — "]:
        if sep in clean:
            artist, song = clean.split(sep, 1)
            return artist.strip(), song.strip()

    # Fallback: usa o texto inteiro como título
    return "", clean

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", required=True, help="JSON de entrada")
    parser.add_argument("--dry-run", action="store_true", help="Mostra o que seria feito")
    parser.add_argument("--threshold", type=float, default=0.6, help="Similaridade mínima para aceitar (0-1)")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay entre buscas (segundos)")
    args = parser.parse_args()

    json_path = Path(args.json)
    if not json_path.exists():
        print(f"❌ JSON não encontrado: {json_path}")
        sys.exit(1)

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    segments = data.get("segments", [])
    print(f"🔍 Processando {len(segments)} segmentos com DuckDuckGo...\n")

    updates = []
    for idx, seg in enumerate(segments):
        current = seg.get("artist", "")
        if " - " in current:
            old_artist, old_title = current.split(" - ", 1)
        else:
            old_artist = ""
            old_title = current

        # Se não tiver título, usa o início da letra
        if not old_title:
            text = seg.get("text", "")
            old_title = text[:60].strip().replace("\n", " ") if text else ""

        query = f"{old_artist} {old_title} cancion" if old_artist else f"{old_title} cancion"
        print(f"[{idx+1:02d}/{len(segments):02d}] {query}")

        results = search_ddg(query, max_results=3)
        if not results:
            print("   ❌ Nenhum resultado.")
            continue

        best = None
        best_score = 0
        for r in results:
            title = r.get("title", "")
            snippet = r.get("body", "")
            new_artist, new_title = extract_artist_title(title)

            # Tenta extrair do snippet se falhou no título
            if not new_artist and not new_title:
                new_artist, new_title = extract_artist_title(snippet)

            # Se ainda não tem, usa o título bruto
            if not new_artist and not new_title:
                new_artist = ""
                new_title = title

            score = similarity(old_title, new_title) if old_title and new_title else 0.5

            if score > best_score:
                best_score = score
                best = {
                    "title": title,
                    "artist": new_artist,
                    "song": new_title,
                    "url": r.get("href", ""),
                    "score": score
                }

        if not best or best_score < args.threshold:
            print(f"   ⚠️ Nenhum candidato com similaridade >= {args.threshold} (melhor: {best_score:.2f})")
            continue

        new_entry = f"{best['artist']} - {best['song']}" if best['artist'] else best['song']
        if new_entry == current:
            print(f"   ✅ Já está correto: {new_entry}")
            continue

        updates.append({
            "index": idx,
            "old": current,
            "new": new_entry,
            "url": best["url"],
            "score": best_score
        })
        print(f"   🔄 {current} → {new_entry} (score: {best_score:.2f})")

        time.sleep(args.delay)

    if args.dry_run:
        print("\n📋 DRY-RUN: mudanças propostas:")
        for u in updates:
            print(f"  [{u['index']}] {u['old']} → {u['new']} (score: {u['score']:.2f})")
        print("\n✅ Nenhuma alteração salva. Remova --dry-run para aplicar.")
        return

    if not updates:
        print("\n✅ Nenhuma atualização necessária.")
        return

    print("\n📝 Aplicando mudanças...")
    for u in updates:
        segments[u["index"]]["artist"] = u["new"]
        segments[u["index"]]["ddg_url"] = u["url"]
        segments[u["index"]]["ddg_score"] = u["score"]

    backup_path = json_path.with_suffix(".json.bak")
    json_path.rename(backup_path)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\n✅ JSON atualizado. Backup em {backup_path}")

if __name__ == "__main__":
    main()
