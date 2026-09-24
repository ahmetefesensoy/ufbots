"""Uzun BVH kliplerini vurusun oldugu ana gore keser.

CMU klipleri genelde uzun ve karisik: 83 saniyelik dosyada diz vurusu
sadece 36. saniyede. Egitime tum klibi vermek hem israf hem zararli
(robot 80 saniye yurumeyi ogrenir, 3 saniye vurmayi).

analyze_bvh.py'nin buldugu `tepe_s` degerini merkez alip etrafindan
kisa bir pencere keser.

Kullanim:
    python scripts/trim_bvh.py                    # analiz CSV'sine gore
    python scripts/trim_bvh.py --window 4         # 4 sn'lik pencere
    python scripts/trim_bvh.py --only UYGUN HAVADA
"""
import argparse
from pathlib import Path

import pandas as pd

SRC = Path("data/combat_bvh")
DST = Path("data/combat_trimmed")
CSV = Path("data_prep/bvh_analiz.csv")


def trim(path: Path, center_s: float, window_s: float, dest: Path):
    """BVH'yi [center - w/2, center + w/2] araligina keser, basligi korur."""
    lines = path.read_text(errors="replace").splitlines()

    # MOTION blogunu bul
    mi = next(i for i, l in enumerate(lines) if l.strip().startswith("MOTION"))
    fi = next(i for i in range(mi, mi + 5) if lines[i].strip().startswith("Frames:"))
    ti = next(i for i in range(mi, mi + 5) if lines[i].strip().startswith("Frame Time:"))
    ft = float(lines[ti].split(":")[1])
    start_data = ti + 1

    frames = [l for l in lines[start_data:] if l.strip()]
    n = len(frames)

    half = int(window_s / ft / 2)
    c = int(center_s / ft)
    a = max(0, c - half)
    b = min(n, c + half)
    if b - a < 30:                      # cok kisaysa bastan al
        a, b = 0, min(n, int(window_s / ft))

    cut = frames[a:b]
    out = lines[:fi] + [f"Frames: {len(cut)}", lines[ti]] + cut
    dest.write_text("\n".join(out) + "\n")
    return len(cut), len(cut) * ft


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--window", type=float, default=4.0, help="pencere uzunlugu (sn)")
    ap.add_argument("--only", nargs="+", default=["UYGUN", "HAVADA"],
                    help="hangi durumlar kesilsin")
    ap.add_argument("--min-len", type=float, default=6.0,
                    help="bu sureden kisa klipler oldugu gibi kopyalanir")
    args = ap.parse_args()

    if not CSV.exists():
        raise SystemExit(f"{CSV} yok — once analyze_bvh.py --csv calistir")
    df = pd.read_csv(CSV)
    df = df[df.durum.isin(args.only)]

    DST.mkdir(parents=True, exist_ok=True)
    total = 0.0
    for _, r in df.iterrows():
        src = SRC / r.dosya
        if not src.exists():
            continue
        dest = DST / r.dosya

        if r.sure_s <= args.min_len:
            # zaten kisa — dokunma
            dest.write_bytes(src.read_bytes())
            print(f"  {r.dosya:<32} {r.sure_s:5.1f}s  (oldugu gibi)")
            total += r.sure_s
        else:
            nk, sn = trim(src, float(r.tepe_s), args.window, dest)
            print(f"  {r.dosya:<32} {r.sure_s:5.1f}s -> {sn:4.1f}s  (tepe {r.tepe_s}s)")
            total += sn

    print(f"\n{len(df)} klip -> {DST}/")
    print(f"toplam sure: {total:.0f} s (once 714 s)")


if __name__ == "__main__":
    main()
