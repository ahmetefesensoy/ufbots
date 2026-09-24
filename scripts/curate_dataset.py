"""Egitim setini kalite puanina gore ayiklar ve agirlıklandirir.

Her klibe 0-100 arasi puan verir:

  dik%      robot govdesini dik tutuyor mu (en agirlikli kriter)
  jitter    kare arasi titreme — dusuk iyi
  ayak_z    kalca cok alcaga dusmus mu (cokme)
  genlik    hareket gercekten var mi (diz/kalca acisi)

Cikti:
  - `train/`   puani esigi gecen klipler
  - `review/`  sinirda olanlar (elle bakilmali)
  - `rejected/` elenenler + sebep
  - `manifest.json` puan tablosu + egitim agirliklari

Neden agirlik: SONIC fine-tune'da tum klipler esit orneklenirse 6 ucan
tekme 27 sıradan hareketin icinde kaybolur. Imza hareketlere daha yuksek
agirlik verilir.

Kullanim:
    python scripts/curate_dataset.py
    python scripts/curate_dataset.py --min-score 60
"""
import argparse
import json
import pickle
import shutil
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation as R

SRC = Path("C:/ufbots_tools/data/g1_polished")
DST = Path("C:/ufbots_tools/data/g1_curated")

# Imza hareketler — egitimde daha sik orneklensin
SIGNATURE = {"chanleak": 3.0, "knee_combo": 2.5, "dum_chanleak": 2.0, "seah": 2.0}
FAMILY_BOOST = {"jump_kick": 2.0, "knee_strike": 2.0, "jump_spin_kick": 0.5}


def measure(d: dict) -> dict:
    pos = np.asarray(d["root_pos"]); quat = np.asarray(d["root_rot"])
    dof = np.rad2deg(np.asarray(d["dof_pos"]))
    rr = R.from_quat(quat[:, [1, 2, 3, 0]])
    up = np.array([rr[i].apply([0, 0, 1])[2] for i in range(len(quat))])
    z = pos[:, 2]
    return {
        "kare": len(pos),
        "dik": float(np.mean(up > 0.8) * 100),
        "jitter": float(np.abs(np.diff(dof, axis=0, n=2)).mean()) if len(dof) > 2 else 0.0,
        "z_min": float(z.min()),
        "sicrama": float(z.max() / (np.median(z) + 1e-9)),
        "diz": float(max(np.ptp(dof[:, 3]), np.ptp(dof[:, 9]))),
        "genlik": float(dof.std()),
    }


def score(m: dict) -> tuple[float, list[str]]:
    """0-100 puan + sorun listesi."""
    notes = []
    # dik durus: 0.8 alti ceza, 0.95 ustu tam puan  (40 puan)
    s_dik = np.clip((m["dik"] - 60) / 35, 0, 1) * 40
    if m["dik"] < 90:
        notes.append(f"dik%{m['dik']:.0f}")
    # jitter: 0.5 alti tam, 2.0 ustu sifir           (25 puan)
    s_jit = np.clip((2.0 - m["jitter"]) / 1.5, 0, 1) * 25
    if m["jitter"] > 1.2:
        notes.append(f"jitter{m['jitter']:.1f}")
    # cokme: 0.55 alti ceza                          (20 puan)
    s_z = np.clip((m["z_min"] - 0.35) / 0.25, 0, 1) * 20
    if m["z_min"] < 0.50:
        notes.append(f"alcak{m['z_min']:.2f}")
    # genlik: hareket var mi                          (15 puan)
    s_amp = np.clip(m["genlik"] / 25, 0, 1) * 15
    if m["genlik"] < 12:
        notes.append("durgun")
    return float(s_dik + s_jit + s_z + s_amp), notes


def weight(stem: str, sc: float) -> float:
    """Egitim ornekleme agirligi."""
    w = SIGNATURE.get(stem, 1.0)
    for fam, mult in FAMILY_BOOST.items():
        if stem.startswith(fam):
            w *= mult
            break
    return round(w * (sc / 100), 2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(SRC))
    ap.add_argument("--dst", default=str(DST))
    ap.add_argument("--min-score", type=float, default=55)
    ap.add_argument("--review-band", type=float, default=10)
    args = ap.parse_args()

    src, dst = Path(args.src), Path(args.dst)
    files = sorted(src.glob("*.pkl"))
    if not files:
        raise SystemExit(f"PKL yok: {src}  — once polish_motions.py")

    for sub in ("train", "review", "rejected"):
        (dst / sub).mkdir(parents=True, exist_ok=True)

    rows = []
    for f in files:
        d = pickle.load(open(f, "rb"))
        m = measure(d)
        sc, notes = score(m)
        if sc >= args.min_score:
            bucket = "train"
        elif sc >= args.min_score - args.review_band:
            bucket = "review"
        else:
            bucket = "rejected"
        shutil.copy2(f, dst / bucket / f.name)
        rows.append({"klip": f.stem, "puan": round(sc, 1), "grup": bucket,
                     "agirlik": weight(f.stem, sc) if bucket == "train" else 0,
                     "not": ",".join(notes), **{k: round(v, 2) for k, v in m.items()}})

    rows.sort(key=lambda r: -r["puan"])
    print(f"{'klip':<26}{'puan':>6}{'grup':>10}{'agirlik':>9}  sorun")
    print("-" * 74)
    for r in rows:
        print(f"{r['klip']:<26}{r['puan']:>6.1f}{r['grup']:>10}{r['agirlik']:>9.2f}  {r['not']}")

    from collections import Counter
    c = Counter(r["grup"] for r in rows)
    print(f"\ntrain {c['train']} | review {c['review']} | rejected {c['rejected']}")
    tot = sum(r["kare"] for r in rows if r["grup"] == "train")
    print(f"egitim suresi: {tot/30:.0f} s")

    (dst / "manifest.json").write_text(
        json.dumps({"min_score": args.min_score, "kliplar": rows}, indent=1, ensure_ascii=False),
        encoding="utf-8")
    print(f"\n-> {dst}  (manifest.json puan tablosu)")


if __name__ == "__main__":
    main()
