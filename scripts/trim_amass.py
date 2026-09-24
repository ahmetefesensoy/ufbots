"""AMASS SMPL-X kliplerini vurus anina gore keser.

BVH tarafinda yaptigimiz kesmenin (trim_bvh.py) SMPL-X karsiligi.
Ayni `tepe_s` degerlerini kullanir — boylece iki veri yolu ayni
hareketleri gosterir.

Kesilen alanlar: trans, poses, root_orient, pose_body, pose_hand,
pose_jaw, pose_eye. Digerleri (betas, gender, ...) oldugu gibi kalir.

Kullanim:
    python scripts/trim_amass.py
    python scripts/trim_amass.py --window 4
"""
import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd

SRC = Path("data/amass_combat")
DST = Path("data/amass_trimmed")
CSV = Path("data_prep/bvh_analiz.csv")

# Zaman ekseni olan alanlar (ilk boyut = kare sayisi)
TIME_KEYS = ["trans", "poses", "root_orient", "pose_body",
             "pose_hand", "pose_jaw", "pose_eye", "dmpls"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--window", type=float, default=4.0)
    ap.add_argument("--min-len", type=float, default=6.0,
                    help="bu sureden kisa klipler oldugu gibi kopyalanir")
    args = ap.parse_args()

    if not CSV.exists():
        raise SystemExit(f"{CSV} yok — once analyze_bvh.py calistir")
    df = pd.read_csv(CSV)

    # analiz CSV'si BVH adlariyla: knee_strike_086_06.bvh
    # AMASS dosyalari sifirsiz:    knee_strike_86_06.npz
    peaks = {}
    for _, r in df.iterrows():
        m = re.search(r"_(\d{3})_(\d{2})\.bvh$", r.dosya)
        if m:
            peaks[f"{int(m.group(1))}_{m.group(2)}"] = (float(r.tepe_s), float(r.sure_s))

    files = sorted(SRC.glob("*.npz"))
    if not files:
        raise SystemExit(f"{SRC} bos — once extract_amass.py calistir")

    DST.mkdir(parents=True, exist_ok=True)
    total = 0.0
    for f in files:
        m = re.search(r"_(\d+)_(\d+)\.npz$", f.name)
        key = f"{int(m.group(1))}_{m.group(2)}" if m else None
        z = dict(np.load(f, allow_pickle=True))

        fps = float(z.get("mocap_frame_rate", 120.0))
        n = len(z["trans"])
        dur = n / fps

        if key not in peaks or dur <= args.min_len:
            np.savez(DST / f.name, **z)
            print(f"  {f.name:<32} {dur:5.1f}s  (oldugu gibi)")
            total += dur
            continue

        peak_s, _ = peaks[key]
        half = int(args.window * fps / 2)
        c = int(peak_s * fps)
        a, b = max(0, c - half), min(n, c + half)
        if b - a < 30:
            a, b = 0, min(n, int(args.window * fps))

        for k in TIME_KEYS:
            if k in z and hasattr(z[k], "shape") and z[k].ndim >= 1 and len(z[k]) == n:
                z[k] = z[k][a:b]
        z["mocap_time_length"] = np.array((b - a) / fps)

        np.savez(DST / f.name, **z)
        print(f"  {f.name:<32} {dur:5.1f}s -> {(b-a)/fps:4.1f}s  (tepe {peak_s}s)")
        total += (b - a) / fps

    mb = sum(p.stat().st_size for p in DST.glob("*.npz")) / 1024 / 1024
    print(f"\n{len(files)} klip -> {DST}/")
    print(f"toplam sure: {total:.0f} s   boyut: {mb:.0f} MB")


if __name__ == "__main__":
    main()
