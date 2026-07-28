#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# Arquivo        : full_mix_analysis.py
# Diretorio      : scripts/
# Responsabilidade:
#   Analisa um mix de audio completo de ponta a ponta: segmenta por
#   BPM/timbre (packages/adaptation/mix_segmentation.py) e transcreve cada
#   segmento (packages/lyrics/transcriber_cpp.py, whisper.cpp local).
#   Produz um JSON estruturado com fronteiras + letra por trecho, pronto
#   para identificacao manual de artista/obra e alimentacao de
#   packages/catalog + packages/publisher/royalties.py.
#
#   NAO identifica artista automaticamente - isso e decisao de negocio em
#   aberto (ver docs/GAPS_NEGOCIO.md e docs/MIX_ANALYSIS.md).
# Versao         : 1.0.0
# Data/hora      : 2026-07-26
# Autoria        : MELO / GOS3 - Scrum . Agile . DevOps
# -----------------------------------------------------------------------------
"""
Uso:
    python scripts/full_mix_analysis.py caminho/mix.wav --out output/analise.json

Pre-requisitos:
    - WAV mono 16kHz (converta de MP3 antes: ver docs/USER_GUIDE.md)
    - whisper.cpp compilado em ~/whisper.cpp/build/bin/whisper-cli
      (ou defina WHISPER_CPP_BIN - ver packages/lyrics/transcriber_cpp.py)
"""
import argparse
import json
import tempfile
from dataclasses import asdict
from pathlib import Path

import soundfile as sf

from packages.adaptation.mix_segmentation import segment_audio_mix
from packages.lyrics.transcriber_cpp import transcribe_audio


def extract_clip(src_path: str, start_sec: float, end_sec: float, out_path: str) -> None:
    """Corta um trecho do WAV original via soundfile (sem dependencia extra de ffmpeg)."""
    y, sr = sf.read(src_path, always_2d=False)
    if getattr(y, "ndim", 1) > 1:
        y = y.mean(axis=1)
    i0, i1 = int(start_sec * sr), int(end_sec * sr)
    sf.write(out_path, y[i0:i1], sr)


_ALUCINACOES_CONHECIDAS = ("suscríbete", "suscribete", "subscribe", "like and subscribe")


def _filtrar_alucinacao_conhecida(texto: str) -> str:
    """Whisper tem alucinacao documentada em trechos instrumentais/silenciosos,
    tipicamente inserindo frases de call-to-action de video (ex: pedidos de
    inscricao em canal) que nao existem no audio real. Marca como [MUSICA]
    em vez de aceitar como transcricao real quando o texto e dominado por
    esses padroes conhecidos.
    """
    baixo = texto.lower().strip()
    if not baixo:
        return texto
    if any(padrao in baixo for padrao in _ALUCINACOES_CONHECIDAS):
        # se o texto e majoritariamente so a alucinacao (poucas palavras
        # alem do padrao conhecido), marca como instrumental
        palavras = baixo.split()
        if len(palavras) <= 6:
            return "[MÚSICA] (transcrição descartada: padrão de alucinação conhecido do Whisper)"
    return texto


def analyze_mix(
    wav_path: str,
    min_seg_sec: float = 20.0,
    max_segments: int = 200,
    modelo: str = "small",
    idioma: str = "es",
) -> list:
    """Segmenta o mix inteiro e transcreve cada segmento. Retorna lista de
    dicts prontos para serializacao (fronteiras + BPM + transcricao)."""
    segments = segment_audio_mix(
        wav_path, min_seg_sec=min_seg_sec, max_segments=max_segments,
    )

    resultados = []
    with tempfile.TemporaryDirectory() as tmpdir:
        for seg in segments:
            clip_path = str(Path(tmpdir) / f"seg_{seg.indice:03d}.wav")
            extract_clip(wav_path, seg.start_sec, seg.end_sec, clip_path)
            try:
                texto = transcribe_audio(clip_path, modelo=modelo, idioma=idioma)
                texto = _filtrar_alucinacao_conhecida(texto)
            except Exception as e:
                texto = f"[ERRO transcricao: {e}]"

            d = asdict(seg)
            d["transcricao"] = texto
            d["modelo_usado"] = modelo
            d["artist_hint"] = None
            d["artist"] = None
            d["work"] = None
            d["label"] = None
            d["beneficiary"] = None
            d["royalty_pct"] = None
            resultados.append(d)

    return resultados


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wav_path", help="Caminho do WAV completo (16kHz mono)")
    parser.add_argument("--out", required=True, help="Caminho do JSON de saida")
    parser.add_argument("--min-seg-sec", type=float, default=20.0)
    parser.add_argument("--max-segments", type=int, default=200)
    parser.add_argument(
        "--modelo", default="small",
        help="Modelo whisper: tiny/base/small/medium/large-v3 "
             "(tiny = mais rapido, recomendado para varredura inicial em arquivo longo)",
    )
    parser.add_argument("--idioma", default="es")
    args = parser.parse_args()

    print(f"[1/2] Segmentando {args.wav_path} ...")
    if args.modelo == "tiny":
        print(
            "    [aviso] modelo 'tiny' tem risco documentado de alucinacao "
            "(inventa palavras/nomes plausiveis em trechos ambiguos/ruidosos). "
            "OK para varredura inicial de fronteiras/BPM. NAO use a transcricao "
            "resultante para atribuicao de autoria/artista sem reprocessar os "
            "segmentos relevantes com --modelo small ou maior."
        )
    resultados = analyze_mix(
        args.wav_path,
        min_seg_sec=args.min_seg_sec,
        max_segments=args.max_segments,
        modelo=args.modelo,
        idioma=args.idioma,
    )
    print(f"  {len(resultados)} segmentos processados")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)

    print(f"\n==> Salvo em {out_path} - {len(resultados)} segmentos com transcricao.")
    print("    Campos artist/work/label/beneficiary/royalty_pct ainda vazios -")
    print("    preencher manualmente ou via integracao de fingerprinting futura.")


if __name__ == "__main__":
    main()
