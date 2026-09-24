"""Bokator kombinasyonlarini birlestirir.

Tek hareket yerine dizi kurar: durus -> giris -> vurus -> inis -> gard.
Klipler arasinda yumusak gecis yapar (kok pozisyonu hizalar, eklem
acilarini harmanlar).

Bokator mantigi: yakin mesafe, dirsek/diz, denge bozma.

Kombinasyonlar (BOKATOR-KOMBINASYON.md):
  chanleak  : dovus durusu -> ileri adim -> UCAN DIZ -> inis -> gard
  seah      : alcak durus -> ileri patlama -> ardisik tekme (at stili)
  knee_combo: gard -> ayakta diz -> tekme

Kullanim:
    python scripts/build_combo.py --list          # tarifleri goster
    python scripts/build_combo.py                 # hepsini kur
    python scripts/build_combo.py --combo chanleak
"""
import argparse
import pickle
from pathlib import Path

import numpy as np

SRC = Path("C:/ufbots_tools/data/g1_smart")
DST = Path("C:/ufbots_tools/data/g1_combos")

# Her adim: (klip, baslangic_orani, bitis_orani)
# Oranlar klibin hangi kismini alacagimizi soyler (0.0-1.0)
COMBOS = {
    "chanleak": [
        ("front_kick_135_04", 0.00, 0.25),   # dovus durusu / giris
        ("jump_kick_75_16",   0.20, 0.85),   # UCAN DIZ (diz 149, sicrama 1.48)
        ("attack_sequence_76_01", 0.30, 0.70),  # inis / gard
    ],
    "seah": [                                  # at stili: ileri yuklenme
        ("kick_74_04",             0.00, 0.40),
        ("punch_kick_combo_141_14", 0.15, 0.75),
        ("kick_74_06",             0.30, 0.70),
    ],
    "knee_combo": [
        ("attack_sequence_76_01", 0.20, 0.55),  # gard
        ("knee_strike_86_06",     0.25, 0.80),  # ayakta diz (120 derece)
        ("front_kick_144_09",     0.30, 0.70),  # takip tekmesi
    ],
    "dum_chanleak": [                           # dirsek + diz (dirsek dolayli)
        ("punch_143_23",      0.30, 0.65),      # dirsek acisi 130
        ("knee_strike_86_06", 0.30, 0.75),
        ("jump_kick_90_05",   0.25, 0.80),
    ],
}

BLEND = 8  # gecis icin harmanlanacak kare sayisi


def load(name: str):
    p = SRC / f"{name}.pkl"
    if not p.exists():
        raise SystemExit(f"klip yok: {p}")
    d = pickle.load(open(p, "rb"))
    return d["root_pos"], d["root_rot"], d["dof_pos"], float(np.asarray(d["fps"]))


def slice_frac(a: np.ndarray, lo: float, hi: float):
    n = len(a)
    return a[int(n * lo):int(n * hi)]


def blend(a: np.ndarray, b: np.ndarray, k: int) -> np.ndarray:
    """a'nin sonu ile b'nin basini k kare boyunca harmanlar."""
    k = min(k, len(a), len(b))
    if k == 0:
        return np.vstack([a, b])
    w = np.linspace(0, 1, k).reshape(-1, 1)
    mid = a[-k:] * (1 - w) + b[:k] * w
    return np.vstack([a[:-k], mid, b[k:]])


def build(steps) -> dict:
    pos_parts, rot_parts, dof_parts, fps = [], [], [], 30.0
    for name, lo, hi in steps:
        rp, rr, dp, f = load(name)
        fps = f
        pos_parts.append(slice_frac(rp, lo, hi))
        rot_parts.append(slice_frac(rr, lo, hi))
        dof_parts.append(slice_frac(dp, lo, hi))

    # Eklemler: harmanlayarak birlestir
    dof = dof_parts[0]
    for nxt in dof_parts[1:]:
        dof = blend(dof, nxt, BLEND)

    # Kok donusu de harmanlanir
    rot = rot_parts[0]
    for nxt in rot_parts[1:]:
        rot = blend(rot, nxt, BLEND)
    rot /= np.linalg.norm(rot, axis=1, keepdims=True)   # quaternion normalize

    # Kok konumu: her parca oncekinin bittigi yerden devam etsin
    pos = pos_parts[0].copy()
    for nxt in pos_parts[1:]:
        shift = pos[-1] - nxt[0]
        shift[2] = 0                      # yukseklik kaydirma — sicramayi bozma
        pos = blend(pos, nxt + shift, BLEND)

    n = min(len(pos), len(rot), len(dof))
    return {"fps": np.array(fps), "root_pos": pos[:n],
            "root_rot": rot[:n], "dof_pos": dof[:n]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--combo", help="tek kombinasyon kur")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--dst", default=str(DST))
    args = ap.parse_args()

    if args.list:
        for k, steps in COMBOS.items():
            print(f"\n{k}:")
            for name, lo, hi in steps:
                print(f"    {name:<26} {lo:.0%}-{hi:.0%}")
        return

    dst = Path(args.dst)
    dst.mkdir(parents=True, exist_ok=True)
    names = [args.combo] if args.combo else list(COMBOS)

    for k in names:
        if k not in COMBOS:
            raise SystemExit(f"bilinmeyen: {k}  ({', '.join(COMBOS)})")
        d = build(COMBOS[k])
        out = dst / f"{k}.pkl"
        pickle.dump(d, open(out, "wb"))

        j = np.rad2deg(d["dof_pos"])
        z = d["root_pos"][:, 2]
        diz = max(np.ptp(j[:, 3]), np.ptp(j[:, 9]))
        print(f"{k:<14} {len(d['root_pos']):4d} kare "
              f"({len(d['root_pos'])/float(d['fps']):.1f}s)  "
              f"diz={diz:.0f}°  sicrama={z.max()/np.median(z):.2f}")

    print(f"\n-> {dst}")


if __name__ == "__main__":
    main()
