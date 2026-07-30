#!/usr/bin/env python3
"""
Enriquece o catálogo usando DuckDuckGo (scraping HTML, sem API).
Uso: python scripts/ddg_scraper.py --json melo-transcription-*.json --dry-run
"""
import json
import sys
import re
import time
from pathlib import Path
from difflib import SequenceMatcher

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("❌ Instale: pip install requests beautifulsoup4")
    sys.exit(1)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

def normalize(text):
    import unicodedata
    text = unicodedata.normalize("NFD", text)
    text = re.sub(r"[\u0300-\u036f]", "", text)
    text = re.sub(r"[^\w\s]", "", text)
    return text.lower().strip()

def similarity(a, b):
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()

def search_ddg(query, max_results=3):
    """Busca no DuckDuckGo via scraping HTML."""
    url = "https://html.duckduckgo.com/html/"
    params = {"q": query}
    headers = {"User-Agent": USER_AGENT}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        results = []
        for result in soup.select(".result")[:max_results]:
            title_tag = result.select_one(".result__a")
            snippet_tag = result.select_one(".result__snippet")
            title = title_tag.get_text(strip=True) if title_tag else ""
            snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
            link = title_tag.get("href") if title_tag else ""
            results.append({"title": title, "body": snippet, "href": link})
        return results
    except Exception as e:
        print(f"   ⚠️ Erro na busca: {e}")
        return []

def extract_artist_title(text):
    clean = re.sub(r"[\(\[].*?[\)\]]", "", text)
    clean = re.sub(r"(Video Oficial|Official Video|Lyric|Audio|Remix|Cover|En Vivo|Live)", "", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\s+", " ", clean).strip()
    for sep in [" - ", " – ", " — "]:
        if sep in clean:
            artist, song = clean.split(sep, 1)
            return artist.strip(), song.strip()
    return "", clean

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument("--delay", type=float, default=1.0)
    args = parser.parse_args()

    json_path = Path(args.json)
    if not json_path.exists():
        print(f"❌ JSON não encontrado: {json_path}")
        sys.exit(1)

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    segments = data.get("segments", [])
    print(f"🔍 Processando {len(segments)} segmentos via DuckDuckGo scraping...\n")

    updates = []
    for idx, seg in enumerate(segments):
        current = seg.get("artist", "")
        if " - " in current:
            old_artist, old_title = current.split(" - ", 1)
        else:
            old_artist = ""
            old_title = current

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
            if not new_artist and not new_title:
                new_artist, new_title = extract_artist_title(snippet)
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
            print(f"   ⚠️ Melhor score: {best_score:.2f} (< {args.threshold})")
            continue

        new_entry = f"{best['artist']} - {best['song']}" if best['artist'] else best['song']
        if new_entry == current:
            print(f"   ✅ Já correto: {new_entry}")
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
        print("\n📋 DRY-RUN:")
        for u in updates:
            print(f"  [{u['index']}] {u['old']} → {u['new']}")
        print("\n✅ Remova --dry-run para aplicar.")
        return

    if not updates:
        print("\n✅ Nenhuma atualização necessária.")
        return

    print("\n📝 Aplicando...")
    for u in updates:
        segments[u["index"]]["artist"] = u["new"]
        segments[u["index"]]["ddg_url"] = u["url"]
        segments[u["index"]]["ddg_score"] = u["score"]

    backup = json_path.with_suffix(".json.bak")
    json_path.rename(backup)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\n✅ JSON atualizado. Backup em {backup}")

if __name__ == "__main__":
    main()
