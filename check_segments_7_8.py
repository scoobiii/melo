import json
import glob

for fpath in sorted(glob.glob("output/*.json")):
    try:
        d = json.load(open(fpath, encoding="utf-8"))
    except Exception as e:
        print(f"{fpath}: erro ao ler ({e})")
        continue
    if not isinstance(d, list):
        print(f"{fpath}: não é lista de segmentos (formato diferente, pulando)")
        continue
    print(f"=== {fpath} ({len(d)} segmentos) ===")
    for s in d:
        if not isinstance(s, dict):
            continue
        idx = s.get("indice")
        if idx in (6, 7, 8):
            inicio = s.get("start_sec")
            fim = s.get("end_sec")
            modelo = s.get("modelo_usado", "?")
            texto = (s.get("transcricao") or "")[:250]
            print(f"  [{idx}] {inicio}-{fim}s | modelo={modelo}")
            print(f"      {texto}")
