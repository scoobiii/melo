#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

echo "==> MELO :: fechando gaps de cobertura (baseado em análise real do código)"

# ============================================================
# 1. segmentation.py:51 — código morto confirmado, marca com pragma
# ============================================================
python3 << 'PYEOF'
from pathlib import Path

path = Path("packages/adaptation/segmentation.py")
content = path.read_text(encoding="utf-8")

old = '''    blocos_brutos = [b.strip() for b in texto_bruto.strip().split("\\n\\n") if b.strip()]
    if not blocos_brutos:
        raise ValueError("Nenhum bloco encontrado após normalizar quebras de linha")'''

new = '''    blocos_brutos = [b.strip() for b in texto_bruto.strip().split("\\n\\n") if b.strip()]
    if not blocos_brutos:  # pragma: no cover
        # Inalcançável dado o código atual: se texto_bruto.strip() (linha
        # acima) é truthy, ao menos um caractere não-whitespace existe no
        # texto original, e ele necessariamente sobrevive em algum bloco
        # após o split + strip individual — logo blocos_brutos nunca fica
        # vazio aqui. Mantido como rede de segurança caso a lógica de split
        # mude no futuro (ex.: separador diferente de "\\n\\n").
        raise ValueError("Nenhum bloco encontrado após normalizar quebras de linha")'''

if old not in content:
    raise SystemExit("[segmentation.py] Trecho esperado não encontrado — abortando sem alterar.")
path.write_text(content.replace(old, new), encoding="utf-8")
print("==> segmentation.py: linha morta marcada com pragma + comentário explicativo.")
PYEOF

# ============================================================
# 2. features.py — 4 testes novos: onset curto, janela de BPM inválida,
#    offset além da duração, downmix estéreo
# ============================================================
cat >> tests/unit/test_adaptation_features.py << 'PYEOF'


def test_estimate_bpm_raises_on_very_short_onset_envelope():
    # y curto o bastante para que o envelope de onset tenha menos de 2
    # amostras (frame_len=1024, hop=512 -> precisa de poucos frames).
    y = np.zeros(2000)
    with pytest.raises(ValueError, match="curto demais"):
        estimate_bpm(y, sample_rate=22050)


def test_estimate_bpm_raises_when_bpm_window_invalid_for_short_audio():
    # Áudio com energia real (não silêncio), mas curto o suficiente para
    # que a janela de lags válidos (min_lag..max_lag) colapse.
    rng = np.random.RandomState(42)
    y = rng.rand(4200)  # onset resultante tem ~5 amostras -> max_lag <= min_lag
    with pytest.raises(ValueError, match="Janela de BPM inválida"):
        estimate_bpm(y, sample_rate=22050)
PYEOF

# precisa do import de estimate_bpm nesse arquivo (já deve existir, mas garante)
if ! grep -q "from packages.adaptation.features import" tests/unit/test_adaptation_features.py; then
    sed -i '1i from packages.adaptation.features import estimate_bpm' tests/unit/test_adaptation_features.py
fi
if ! grep -q "^import numpy as np" tests/unit/test_adaptation_features.py; then
    sed -i '1i import numpy as np' tests/unit/test_adaptation_features.py
fi

cat >> tests/unit/test_adaptation_features_window.py << 'PYEOF'


def test_extract_features_raises_when_offset_exceeds_duration(long_audio_file):
    with pytest.raises(ValueError, match="Janela inválida"):
        extract_features(long_audio_file, window_seconds=10.0, offset_seconds=999.0)


def test_extract_features_downmixes_stereo_to_mono(tmp_path):
    sample_rate = 22050
    duration = 10.0
    bpm = 100
    n_samples = int(sample_rate * duration)
    y_mono = np.zeros(n_samples)
    interval = int(sample_rate * 60.0 / bpm)
    for i in range(0, n_samples, interval):
        y_mono[i:i + 50] = 0.8

    y_stereo = np.column_stack([y_mono, np.roll(y_mono, 5)])
    path = tmp_path / "faixa_estereo.wav"
    sf.write(str(path), y_stereo, sample_rate)

    resultado = extract_features(str(path), window_seconds=8.0, offset_seconds=0.0)
    assert resultado.bpm > 0
PYEOF

echo "==> features.py: 4 testes novos adicionados (2 em test_adaptation_features.py, 2 em test_adaptation_features_window.py)."

# ============================================================
# 3. adapter.py:190 — except AdaptationParseError: raise (dentro de adapt())
#    precisa de um response 200 com XML quebrado, via adapter.adapt() de verdade,
#    não via _parse_response() isolado.
# ============================================================
cat >> tests/unit/test_ai_adapter.py << 'PYEOF'


@patch("packages.ai.adapter.requests.post")
def test_adapter_adapt_reraises_parse_error_on_broken_xml(mock_post):
    # Resposta 200 (sucesso HTTP), mas corpo XML sem as tags esperadas —
    # exercita o `except AdaptationParseError: raise` dentro de adapt(),
    # não apenas _parse_response() isolado.
    mock_post.return_value = _mock_response(
        status_code=200,
        content=[{"type": "text", "text": "<analysis><theme>x</theme></analysis>"}],
    )

    adapter = LyricAdapter(api_key="fake-key-for-test")
    with pytest.raises(AdaptationParseError):
        adapter.adapt("letra original", CORRELATION)

    mock_post.assert_called_once()
PYEOF

echo "==> adapter.py: teste do except AdaptationParseError dentro de adapt() adicionado."

# ============================================================
# 4. store.py:107 + 126-133 — caminho NÃO-memória (arquivo real em disco)
#    nunca foi exercitado; todos os testes existentes usam ':memory:'.
# ============================================================
cat >> tests/unit/test_catalog_store.py << 'PYEOF'


def test_catalog_store_with_real_file_creates_parent_dir_and_persists(tmp_path):
    # Exercita o caminho NÃO-memória: cria diretório pai (mkdir), abre/commita/
    # fecha conexão real de arquivo (_connect não-memory), diferente da
    # fixture `store` acima, que só usa ':memory:'.
    db_path = tmp_path / "subdir" / "catalog.sqlite3"
    assert not db_path.parent.exists()

    store_arquivo = CatalogStore(db_path=db_path)
    assert db_path.parent.exists()  # mkdir(parents=True) funcionou

    store_arquivo.add_source_artist("Y", "cumbia_panamena", faixa_original="Faixa B")

    # reabre com uma NOVA instância apontando pro mesmo arquivo, confirmando
    # que os dados persistiram de fato em disco (não só em memória do processo)
    store_reaberto = CatalogStore(db_path=db_path)
    artistas = store_reaberto.list_source_artists(genero_origem="cumbia_panamena")
    assert len(artistas) == 1
    assert artistas[0].nome == "Y"
PYEOF

echo "==> store.py: teste do caminho de arquivo real (não-memória) adicionado."

echo ""
echo "==> Rodando suíte completa + coverage final"
pytest -q
pytest --cov=packages --cov-report=term-missing -q
