"""Egitilmis politika videolarini sirala — dusme var mi, hareket ne kadar genis.

Render'da robot beyaz, zemin gri, referans hedefler sari. Robot pikselleri
(doygunlugu dusuk + parlak) maskelenip her karede:

    tepe   : en ustteki robot pikselinin y'si (dusuk = ayakta)
    yayilim: robotun dikey uzanimi

Dusme tespiti: tepe cizgisi baslangic medyaninin %60'inin altina inerse.

Kullanim:
    python scripts/rank_renders.py results/trained
"""
import argparse
from pathlib import Path

import imageio.v2 as iio
import numpy as np


def robot_mask(fr):
    """Beyaz-gri robot pikselleri: parlak ve renksiz. Sari toplar elenir."""
    f = fr.astype(np.int16)
    r, g, b = f[..., 0], f[..., 1], f[..., 2]
    mx, mn = f.max(2), f.min(2)
    sat = mx - mn
    # sari toplar: r,g yuksek b dusuk -> sat buyuk. robot: sat kucuk.
    return (mx > 155) & (sat < 28) & (b > 130)


def analyse(path: Path, step: int = 3):
    top, area = [], []
    for i, fr in enumerate(iio.get_reader(path)):
        if i % step:
            continue
        m = robot_mask(fr[::3, ::3])
        ys = np.nonzero(m.any(1))[0]
        if len(ys) < 3:
            top.append(np.nan); area.append(0.0); continue
        h = m.shape[0]
        # goruntu koordinatinda y asagi artar -> yukseklik = h - ymin
        top.append((h - ys.min()) / h)
        area.append(float(m.sum()) / m.size)
    t = np.asarray(top, float)
    t = t[~np.isnan(t)]
    if len(t) < 10:
        return None
    base = float(np.median(t[: max(5, len(t) // 10)]))
    lo = float(t.min())
    fell = lo < base * 0.62
    return {
        "kare": len(t),
        "taban": base,
        "min": lo,
        "oran": lo / base,
        "dusme": fell,
        "hareket": float(np.std(t)),
        "alan": float(np.mean(area)),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src", nargs="?", default="results/trained")
    args = ap.parse_args()

    vids = sorted(Path(args.src).glob("*.mp4"))
    if not vids:
        raise SystemExit(f"mp4 yok: {args.src}")

    print(f"{'video':<14}{'kare':>6}{'taban':>8}{'min':>8}{'oran':>7}"
          f"{'hareket':>9}  sonuc")
    print("-" * 62)
    rows = []
    for v in vids:
        r = analyse(v)
        if not r:
            print(f"{v.stem:<14}  okunamadi"); continue
        verdict = "DUSTU" if r["dusme"] else "AYAKTA"
        rows.append((v.stem, r, verdict))
        print(f"{v.stem:<14}{r['kare']:>6}{r['taban']:>8.3f}{r['min']:>8.3f}"
              f"{r['oran']:>7.2f}{r['hareket']:>9.4f}  {verdict}")

    ok = [x for x in rows if x[2] == "AYAKTA"]
    print(f"\nayakta: {len(ok)}/{len(rows)}")
    if ok:
        best = max(ok, key=lambda x: x[1]["hareket"])
        print(f"en genis hareketli ayakta klip: {best[0]} "
              f"(hareket {best[1]['hareket']:.4f})")


if __name__ == "__main__":
    main()
