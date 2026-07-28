import json
import glob

for fpath in sorted(glob.glob("output/*.json")):
    try:
        d = json.load(open(fpath, encoding="utf-8"))
    except Exception:
        continue
    if not isinstance(d, list):
        continue
    achou = False
    for s in d:
        if not isinstance(s, dict):
            continue
        t = (s.get("transcricao") or "")
        if "nicole" in t.lower():
            if not achou:
                print(f"=== {fpath} ===")
                achou = True
            idx = s.get("indice")
            inicio = s.get("start_sec")
            fim = s.get("end_sec")
            modelo = s.get("modelo_usado", "?")
            print(f"  indice {idx}: {inicio}-{fim}s | modelo={modelo}")
            print(f"  texto: {t[:200]}")
