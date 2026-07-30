#!/usr/bin/env python3
"""
MELO — Music Catalog Validator

Objetivo
---------
Validar e enriquecer um catálogo previamente obtido por
transcrição e/ou curadoria manual.

Este script NÃO realiza fingerprinting de áudio.

Ele utiliza artista e título previamente conhecidos para
consultar catálogos públicos (MusicBrainz) e recuperar
metadados oficiais como:

- Recording
- Artist
- Release
- Release Date
- ISRC
- MBIDs

Entrada
--------
melo-transcription-*.json

Saídas
------
output/catalogo_validado.json
output/catalogo_validado.csv
output/catalogo_validado.sqlite
output/pendencias_catalogo.json
output/relatorio_catalogo.md
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sqlite3
import sys
import time
import unicodedata
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
from urllib.parse import quote
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


# ============================================================
# CONFIGURAÇÃO
# ============================================================

APP_NAME = "MELO-Music-Adaptation-Factory"
APP_VERSION = "0.1.0"

USER_AGENT = (
    f"{APP_NAME}/{APP_VERSION} "
    "(catalog-validator; contact=local@localhost)"
)

MUSICBRAINZ_API = "https://musicbrainz.org/ws/2"

REQUEST_INTERVAL = 1.1
REQUEST_TIMEOUT = 20

MIN_AUTO_ACCEPT = 82.0
MIN_REVIEW = 55.0

OUTPUT_DIR = Path("output")


# ============================================================
# MODELO
# ============================================================

@dataclass
class CatalogRecord:
    segment: int
    start_time: str
    end_time: str

    detected_artist: str
    detected_title: str

    normalized_artist: str
    normalized_title: str

    matched_artist: str
    matched_title: str

    confidence: float
    status: str

    mb_recording_id: str
    mb_artist_id: str

    release_title: str
    release_date: str

    isrcs: str

    source_url: str
    notes: str


# ============================================================
# NORMALIZAÇÃO
# ============================================================

TITLE_FIXES = {
    "y lloraras e sufriras": "Y Llorarás y Sufrirás",
    "y lloraras y sufriras": "Y Llorarás y Sufrirás",
}


def strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value)
    return "".join(
        char
        for char in normalized
        if unicodedata.category(char) != "Mn"
    )


def normalize_text(value: str) -> str:
    value = value or ""
    value = strip_accents(value)
    value = value.lower()
    value = re.sub(r"[^\w\s]", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def clean_display(value: str) -> str:
    value = re.sub(r"\s+", " ", value or "")
    return value.strip(" -–—")


def title_correction(title: str) -> str:
    key = normalize_text(title)

    if key in TITLE_FIXES:
        return TITLE_FIXES[key]

    return clean_display(title)


def split_artist_title(value: str) -> tuple[str, str]:
    """
    Aceita:
        Edward Cedeño - Inevitable

    Também aceita:
        Edward Cedeño — Inevitable
        Edward Cedeño – Inevitable

    Se não houver separador:
        artista = ""
        título = valor
    """

    value = clean_display(value)

    parts = re.split(r"\s+[-–—]\s+", value, maxsplit=1)

    if len(parts) == 2:
        artist = clean_display(parts[0])
        title = title_correction(parts[1])
        return artist, title

    return "", title_correction(value)


# ============================================================
# SIMILARIDADE
# ============================================================

def levenshtein_distance(left: str, right: str) -> int:
    if left == right:
        return 0

    if not left:
        return len(right)

    if not right:
        return len(left)

    previous = list(range(len(right) + 1))

    for i, char_left in enumerate(left, start=1):
        current = [i]

        for j, char_right in enumerate(right, start=1):
            insertion = current[j - 1] + 1
            deletion = previous[j] + 1
            substitution = previous[j - 1] + (
                char_left != char_right
            )

            current.append(
                min(insertion, deletion, substitution)
            )

        previous = current

    return previous[-1]


def similarity(left: str, right: str) -> float:
    left = normalize_text(left)
    right = normalize_text(right)

    if not left and not right:
        return 100.0

    if not left or not right:
        return 0.0

    distance = levenshtein_distance(left, right)

    maximum = max(len(left), len(right))

    return round(
        100.0 * (1.0 - distance / maximum),
        2,
    )


# ============================================================
# HTTP
# ============================================================

def request_json(url: str) -> dict[str, Any]:
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        },
    )

    try:
        with urlopen(
            request,
            timeout=REQUEST_TIMEOUT,
        ) as response:

            raw = response.read()

            return json.loads(
                raw.decode("utf-8")
            )

    except HTTPError as error:
        raise RuntimeError(
            f"HTTP {error.code}: {url}"
        ) from error

    except URLError as error:
        raise RuntimeError(
            f"Falha de rede: {error.reason}"
        ) from error


# ============================================================
# MUSICBRAINZ
# ============================================================

def build_query(
    artist: str,
    title: str,
) -> str:

    if artist:
        return (
            f'recording:"{title}" '
            f'AND artist:"{artist}"'
        )

    return f'recording:"{title}"'


def search_musicbrainz(
    artist: str,
    title: str,
    limit: int = 10,
) -> list[dict[str, Any]]:

    query = build_query(
        artist,
        title,
    )

    url = (
        f"{MUSICBRAINZ_API}/recording"
        f"?query={quote(query)}"
        f"&fmt=json"
        f"&limit={limit}"
    )

    data = request_json(url)

    time.sleep(REQUEST_INTERVAL)

    return data.get(
        "recordings",
        [],
    )


def candidate_score(
    detected_artist: str,
    detected_title: str,
    candidate: dict[str, Any],
) -> float:

    candidate_title = candidate.get(
        "title",
        "",
    )

    title_score = similarity(
        detected_title,
        candidate_title,
    )

    artists = candidate.get(
        "artist-credit",
        [],
    )

    candidate_artists = " ".join(
        item.get("name", "")
        for item in artists
        if isinstance(item, dict)
    )

    if detected_artist:
        artist_score = similarity(
            detected_artist,
            candidate_artists,
        )

        score = (
            title_score * 0.65
            + artist_score * 0.35
        )

    else:
        score = title_score

    mb_score = float(
        candidate.get(
            "score",
            0,
        )
    )

    score = (
        score * 0.85
        + mb_score * 0.15
    )

    return round(
        min(score, 100.0),
        2,
    )


def choose_candidate(
    artist: str,
    title: str,
) -> tuple[
    dict[str, Any] | None,
    float,
]:

    candidates = search_musicbrainz(
        artist=artist,
        title=title,
    )

    if not candidates:
        return None, 0.0

    ranked = sorted(
        (
            (
                candidate_score(
                    artist,
                    title,
                    candidate,
                ),
                candidate,
            )
            for candidate in candidates
        ),
        key=lambda item: item[0],
        reverse=True,
    )

    score, candidate = ranked[0]

    return candidate, score


def artist_names(
    candidate: dict[str, Any],
) -> str:

    names = []

    for item in candidate.get(
        "artist-credit",
        [],
    ):
        if isinstance(item, dict):

            name = item.get(
                "name",
                "",
            )

            if name:
                names.append(name)

    return ", ".join(names)


def artist_ids(
    candidate: dict[str, Any],
) -> str:

    ids = []

    for item in candidate.get(
        "artist-credit",
        [],
    ):
        if not isinstance(
            item,
            dict,
        ):
            continue

        artist = item.get(
            "artist",
            {},
        )

        artist_id = artist.get(
            "id",
            "",
        )

        if artist_id:
            ids.append(artist_id)

    return ",".join(ids)


def release_info(
    candidate: dict[str, Any],
) -> tuple[str, str]:

    releases = candidate.get(
        "releases",
        [],
    )

    if not releases:
        return "", ""

    release = sorted(
        releases,
        key=lambda item: (
            item.get("date", "9999-99-99"),
            item.get("title", ""),
        ),
    )[0]

    return (
        release.get("title", ""),
        release.get("date", ""),
    )


# ============================================================
# VALIDAÇÃO
# ============================================================

def validate_segment(
    index: int,
    segment: dict[str, Any],
) -> CatalogRecord:

    detected = clean_display(
        str(
            segment.get(
                "artist",
                "",
            )
        )
    )

    detected_artist, detected_title = (
        split_artist_title(
            detected
        )
    )

    candidate = None
    confidence = 0.0
    error_message = ""

    try:
        candidate, confidence = (
            choose_candidate(
                artist=detected_artist,
                title=detected_title,
            )
        )

    except Exception as error:
        error_message = str(error)

    if candidate is None:

        if error_message:
            status = "NETWORK_ERROR"
            notes = error_message

        else:
            status = "NOT_FOUND"
            notes = (
                "Nenhum candidato encontrado "
                "no catálogo-base."
            )

        return CatalogRecord(
            segment=index,
            start_time=str(
                segment.get(
                    "startTime",
                    "",
                )
            ),
            end_time=str(
                segment.get(
                    "endTime",
                    "",
                )
            ),

            detected_artist=detected_artist,
            detected_title=detected_title,

            normalized_artist=detected_artist,
            normalized_title=detected_title,

            matched_artist="",
            matched_title="",

            confidence=confidence,
            status=status,

            mb_recording_id="",
            mb_artist_id="",

            release_title="",
            release_date="",

            isrcs="",

            source_url="",
            notes=notes,
        )

    matched_artist = artist_names(
        candidate
    )

    matched_title = candidate.get(
        "title",
        "",
    )

    release_title, release_date = (
        release_info(
            candidate
        )
    )

    isrcs = ",".join(
        candidate.get(
            "isrcs",
            [],
        )
    )

    recording_id = candidate.get(
        "id",
        "",
    )

    if confidence >= MIN_AUTO_ACCEPT:

        status = "VALIDATED"

        notes = (
            "Correspondência automática "
            "aceita."
        )

    elif confidence >= MIN_REVIEW:

        status = "REVIEW"

        notes = (
            "Candidato encontrado, "
            "mas exige revisão humana."
        )

    else:

        status = "LOW_CONFIDENCE"

        notes = (
            "Candidato encontrado, "
            "mas a confiança é baixa."
        )

    if not detected_artist:

        notes += (
            " Artista ausente "
            "na transcrição original."
        )

        if status == "VALIDATED":
            status = "REVIEW"

    return CatalogRecord(
        segment=index,

        start_time=str(
            segment.get(
                "startTime",
                "",
            )
        ),

        end_time=str(
            segment.get(
                "endTime",
                "",
            )
        ),

        detected_artist=detected_artist,

        detected_title=detected_title,

        normalized_artist=detected_artist,

        normalized_title=detected_title,

        matched_artist=matched_artist,

        matched_title=matched_title,

        confidence=confidence,

        status=status,

        mb_recording_id=recording_id,

        mb_artist_id=artist_ids(
            candidate
        ),

        release_title=release_title,

        release_date=release_date,

        isrcs=isrcs,

        source_url=(
            "https://musicbrainz.org/recording/"
            f"{recording_id}"
        ),

        notes=notes,
    )


# ============================================================
# EXPORTAÇÃO
# ============================================================

def write_json(
    records: list[CatalogRecord],
    source: dict[str, Any],
) -> Path:

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    path = (
        OUTPUT_DIR
        / "catalogo_validado.json"
    )

    payload = {
        "schema_version": "1.0",

        "source": {
            "title": source.get(
                "title",
                "",
            ),

            "videoUrl": source.get(
                "videoUrl",
                "",
            ),

            "exportedAt": source.get(
                "exportedAt",
                "",
            ),
        },

        "records": [
            asdict(record)
            for record in records
        ],
    }

    path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return path


def write_csv(
    records: list[CatalogRecord],
) -> Path:

    path = (
        OUTPUT_DIR
        / "catalogo_validado.csv"
    )

    rows = [
        asdict(record)
        for record in records
    ]

    if not rows:

        path.write_text(
            "",
            encoding="utf-8",
        )

        return path

    with path.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=rows[0].keys(),
        )

        writer.writeheader()

        writer.writerows(rows)

    return path


def write_sqlite(
    records: list[CatalogRecord],
) -> Path:

    path = (
        OUTPUT_DIR
        / "catalogo_validado.sqlite"
    )

    connection = sqlite3.connect(
        path
    )

    cursor = connection.cursor()

    cursor.execute(
        """
        DROP TABLE IF EXISTS tracks
        """
    )

    cursor.execute(
        """
        CREATE TABLE tracks (
            segment INTEGER PRIMARY KEY,

            start_time TEXT,
            end_time TEXT,

            detected_artist TEXT,
            detected_title TEXT,

            normalized_artist TEXT,
            normalized_title TEXT,

            matched_artist TEXT,
            matched_title TEXT,

            confidence REAL,
            status TEXT,

            mb_recording_id TEXT,
            mb_artist_id TEXT,

            release_title TEXT,
            release_date TEXT,

            isrcs TEXT,

            source_url TEXT,

            notes TEXT
        )
        """
    )

    cursor.execute(
        """
        CREATE INDEX
        idx_tracks_status
        ON tracks(status)
        """
    )

    cursor.execute(
        """
        CREATE INDEX
        idx_tracks_artist
        ON tracks(matched_artist)
        """
    )

    for record in records:

        data = asdict(
            record
        )

        cursor.execute(
            """
            INSERT INTO tracks (
                segment,
                start_time,
                end_time,

                detected_artist,
                detected_title,

                normalized_artist,
                normalized_title,

                matched_artist,
                matched_title,

                confidence,
                status,

                mb_recording_id,
                mb_artist_id,

                release_title,
                release_date,

                isrcs,

                source_url,

                notes
            )
            VALUES (
                :segment,
                :start_time,
                :end_time,

                :detected_artist,
                :detected_title,

                :normalized_artist,
                :normalized_title,

                :matched_artist,
                :matched_title,

                :confidence,
                :status,

                :mb_recording_id,
                :mb_artist_id,

                :release_title,
                :release_date,

                :isrcs,

                :source_url,

                :notes
            )
            """,
            data,
        )

    connection.commit()

    connection.close()

    return path


def write_pending(
    records: list[CatalogRecord],
) -> Path:

    path = (
        OUTPUT_DIR
        / "pendencias_catalogo.json"
    )

    pending = [
        asdict(record)
        for record in records
        if record.status != "VALIDATED"
    ]

    path.write_text(
        json.dumps(
            pending,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return path


def write_report(
    records: list[CatalogRecord],
) -> Path:

    path = (
        OUTPUT_DIR
        / "relatorio_catalogo.md"
    )

    total = len(records)

    validated = sum(
        item.status == "VALIDATED"
        for item in records
    )

    review = sum(
        item.status == "REVIEW"
        for item in records
    )

    not_found = sum(
        item.status == "NOT_FOUND"
        for item in records
    )

    network_errors = sum(
        item.status == "NETWORK_ERROR"
        for item in records
    )

    lines = [
        "# MELO — Relatório de Validação",
        "",
        f"- Total: **{total}**",
        f"- Validados: **{validated}**",
        f"- Revisão: **{review}**",
        f"- Não encontrados: **{not_found}**",
        f"- Erros de rede: **{network_errors}**",
        "",
        "## Pendências",
        "",
    ]

    for item in records:

        if item.status == "VALIDATED":
            continue

        lines.extend(
            [
                (
                    f"### {item.segment:02d} — "
                    f"{item.detected_title}"
                ),
                "",
                f"- Status: `{item.status}`",
                (
                    f"- Confiança: "
                    f"{item.confidence:.2f}%"
                ),
                (
                    f"- Artista detectado: "
                    f"{item.detected_artist or 'AUSENTE'}"
                ),
                (
                    f"- Candidato: "
                    f"{item.matched_artist} — "
                    f"{item.matched_title}"
                ),
                f"- Nota: {item.notes}",
                "",
            ]
        )

    path.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    return path


# ============================================================
# EXECUÇÃO
# ============================================================

def main() -> int:

    parser = argparse.ArgumentParser(
        description=(
            "Valida catálogo musical "
            "exportado pelo MELO."
        )
    )

    parser.add_argument(
        "input",
        type=Path,
        help="JSON de transcrição.",
    )

    arguments = parser.parse_args()

    input_path = arguments.input

    if not input_path.exists():

        print(
            f"ERRO: arquivo não encontrado: "
            f"{input_path}",
            file=sys.stderr,
        )

        return 2

    source = json.loads(
        input_path.read_text(
            encoding="utf-8"
        )
    )

    segments = source.get(
        "segments",
        [],
    )

    if not isinstance(
        segments,
        list,
    ):

        print(
            "ERRO: segments deve ser uma lista.",
            file=sys.stderr,
        )

        return 3

    records = []

    print(
        f"MELO Catalog Validator"
    )

    print(
        f"Faixas: {len(segments)}"
    )

    print()

    for index, segment in enumerate(
        segments,
        start=1,
    ):

        print(
            f"[{index:02d}/{len(segments):02d}] "
            f"{segment.get('artist', '')}",
            flush=True,
        )

        record = validate_segment(
            index=index,
            segment=segment,
        )

        records.append(
            record
        )

        print(
            f"  -> {record.status} "
            f"{record.confidence:.2f}%"
        )

    json_path = write_json(
        records,
        source,
    )

    csv_path = write_csv(
        records
    )

    sqlite_path = write_sqlite(
        records
    )

    pending_path = write_pending(
        records
    )

    report_path = write_report(
        records
    )

    print()

    print("ARQUIVOS GERADOS:")

    for path in [
        json_path,
        csv_path,
        sqlite_path,
        pending_path,
        report_path,
    ]:
        print(f"  {path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
