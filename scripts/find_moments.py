"""Egitim videolarinda dikkat cekici anlari bulur.

Hangi saniyede ne oldugunu tahmin etmek yerine olcuyoruz:
  yukseklik : robot siluetinin tepe noktasi (ziplama/diz yukselisi)
  genislik  : yatay uzanim (tekme/yumruk uzanmasi)

Kullanim:
    python scripts/find_moments.py results/trained/000005.mp4
"""
import argparse
from pathlib import Path

import imageio.v2 as iio
import numpy as np


def robot_mask(fr):
    f = fr.astype(np.int16)
    b = f[..., 2]
    mx, mn = f.max(2), f.min(2)
    return (mx > 155) & ((mx - mn) < 28) & (b > 130)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video"); ap.add_argument("--step", type=int, default=5)
    ap.add_argument("--top", type=int, default=6)
    a = ap.parse_args()

    hi, wide, idx = [], [], []
    for i, fr in enumerate(iio.get_reader(a.video)):
        if i % a.step:
            continue
        m = robot_mask(fr[::4, ::4])
        ys, xs = np.nonzero(m.any(1))[0], np.nonzero(m.any(0))[0]
        if len(ys) < 3 or len(xs) < 3:
            continue
        hi.append(m.shape[0] - ys.min()); wide.append(xs.max() - xs.min())
        idx.append(i)

    hi, wide, idx = np.array(hi), np.array(wide), np.array(idx)
    print(f"{Path(a.video).name}  {len(idx)} ornek\n")
    for label, arr in (("EN YUKSEK (zipla/diz)", hi), ("EN GENIS (tekme/uzanma)", wide)):
        print(label)
        for k in np.argsort(-arr)[: a.top]:
            print(f"   kare {idx[k]:5d}  ({idx[k]/30:5.1f}s)  deger {arr[k]}")
        print()


if __name__ == "__main__":
    main()
