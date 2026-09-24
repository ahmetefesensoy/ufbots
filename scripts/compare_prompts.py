"""Kimodo ciktilarini karsilastirir: model stili gercekten biliyor mu?

Asil soru: "bokator elbow strike" ile "downward elbow strike" ayni seyi mi
uretiyor? Ayni ise model stil ismini tanimyor, sadece jenerik hareket veriyor.

Olcum: eklem acisi zaman serilerini hizalayip ortalama mutlak fark alir.
Kucuk fark = ayni hareket. Buyuk fark = model istemleri ayirt ediyor.

Kullanim:
    python scripts/compare_prompts.py                    # tum ciftler
    python scripts/compare_prompts.py --dir data/kimodo_csv
"""
import argparse
import itertools
from pathlib import Path

import numpy as np
import pandas as pd

# Karsilastirilacak ciftler: (isimle, tarifle)
PAIRS = [
    ("bokator_named", "bokator_desc"),
    ("muaythai_named", "muaythai_desc"),
    ("spin_named", "spin_desc"),
]


def load(path: Path) -> np.ndarray:
    """CSV -> eklem acisi matrisi (frame x dof)."""
    d = pd.read_csv(path)
    cols = [c for c in d.columns if c.endswith("_dof")]
    return d[cols].to_numpy()


def distance(a: np.ndarray, b: np.ndarray) -> float:
    """Iki hareket arasi ortalama mutlak fark (derece).

    Farkli uzunluktaysa kisa olana gore kirpar — kaba ama
    'ayni mi degil mi' sorusu icin yeterli.
    """
    n = min(len(a), len(b))
    if n == 0 or a.shape[1] != b.shape[1]:
        return float("nan")
    return float(np.abs(a[:n] - b[:n]).mean())


def group(files: list[Path]) -> dict[str, list[Path]]:
    """Dosyalari istem adina gore grupla (bokator_named__000.csv -> bokator_named)."""
    out: dict[str, list[Path]] = {}
    for f in files:
        tag = f.stem.split("__")[0]
        out.setdefault(tag, []).append(f)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="data/kimodo_csv")
    args = ap.parse_args()

    root = Path(args.dir)
    files = sorted(root.glob("*.csv"))
    if not files:
        raise SystemExit(f"CSV yok: {root}  — once import_kimodo.py calistir")

    g = group(files)
    print(f"{len(files)} dosya, {len(g)} istem\n")
    for k in sorted(g):
        print(f"  {k:<18} {len(g[k])} ornek")

    # --- 1. Ayni istemin kendi ornekleri arasindaki fark (taban gurultu) ---
    print(f"\n{'='*58}\nAYNI ISTEM, FARKLI ORNEK (taban)\n{'='*58}")
    baseline = []
    for tag, fs in sorted(g.items()):
        if len(fs) < 2:
            continue
        ds = [distance(load(a), load(b)) for a, b in itertools.combinations(fs, 2)]
        ds = [d for d in ds if not np.isnan(d)]
        if ds:
            m = float(np.mean(ds))
            baseline.append(m)
            print(f"  {tag:<18} {m:6.2f} derece")

    base = float(np.mean(baseline)) if baseline else float("nan")
    print(f"\n  ortalama taban: {base:.2f} derece")
    print("  (ayni istemin ornekleri bile bu kadar farkli — gurultu esigi)")

    # --- 2. Isimle vs tarifle ---
    print(f"\n{'='*58}\nISIMLE vs TARIFLE\n{'='*58}")
    for a_tag, b_tag in PAIRS:
        if a_tag not in g or b_tag not in g:
            print(f"  {a_tag} / {b_tag}: dosya eksik, atlandi")
            continue
        ds = [distance(load(a), load(b)) for a in g[a_tag] for b in g[b_tag]]
        ds = [d for d in ds if not np.isnan(d)]
        if not ds:
            continue
        m = float(np.mean(ds))
        # Taban gurultuye gore yorumla
        if np.isnan(base) or base == 0:
            verdict = "?"
        elif m < base * 1.2:
            verdict = "AYNI  -> model stil ismini tanimiyor"
        elif m > base * 2:
            verdict = "FARKLI -> model istemi ayirt ediyor"
        else:
            verdict = "belirsiz"
        print(f"  {a_tag:<16} vs {b_tag:<16} {m:6.2f}  {verdict}")

    print(f"\n{'='*58}")
    print("Not: bu sayisal bir ipucu, karar videolara bakarak verilir.")
    print("  python scripts/preview_mujoco.py --csv <dosya> --video results/x.mp4")


if __name__ == "__main__":
    main()
