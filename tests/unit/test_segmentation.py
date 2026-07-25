# Localização no repo: tests/unit/test_segmentation.py
"""Testes de packages/adaptation/segmentation.py. Puro, sem I/O nenhum."""

import pytest

from packages.adaptation.segmentation import segment_lyrics


def test_segment_lyrics_rejects_empty_text():
    with pytest.raises(ValueError):
        segment_lyrics("")


def test_segment_lyrics_rejects_whitespace_only():
    with pytest.raises(ValueError):
        segment_lyrics("   \n\n   ")


def test_segment_lyrics_single_block_is_verso():
    segmentos = segment_lyrics("uma linha só de letra")
    assert len(segmentos) == 1
    assert segmentos[0].tipo == "verso"


def test_segment_lyrics_repeated_block_is_refrao():
    texto = "verso um\n\nrefrão que repete\n\nverso dois\n\nrefrão que repete"
    segmentos = segment_lyrics(texto)
    tipos = [s.tipo for s in segmentos]
    assert tipos == ["verso", "refrao", "verso", "refrao"]


def test_segment_lyrics_preserves_original_text_not_normalized():
    texto = "Refrão Repete\n\nverso\n\nrefrão repete"
    segmentos = segment_lyrics(texto)
    # o texto original (com maiúsculas) é preservado, só a comparação é normalizada
    assert segmentos[0].texto == "Refrão Repete"
    assert segmentos[2].texto == "refrão repete"
    assert segmentos[0].tipo == "refrao"
    assert segmentos[2].tipo == "refrao"


def test_segment_lyrics_indices_are_sequential():
    texto = "a\n\nb\n\nc"
    segmentos = segment_lyrics(texto)
    assert [s.indice for s in segmentos] == [0, 1, 2]
