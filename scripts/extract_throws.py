"""ReMoCap Ninjutsu'dan ATAN kisinin hareketini cikarir.

Veri iki kisilik: p0 ve p1. Bizim isimize yarayan sadece ATAN kisi —
atilan kisi yere dusuyor, G1 bunu yapamaz (kalkamiyor).

Rol ayrimi kok yuksekligiyle yapildi (data_prep/ninjutsu_clean.json):
    atan   -> kalca medyanin >%60'inda kalir (ayakta)
    atilan -> kalca medyanin <%35'ine duser (yerde)

Atis ani: atilan kisinin en hizli dustugu an. Atan kisinin hareketi
o ana gore kesilir — bokator'daki `Kbach Chhlang` / `jruk tajak`.

Kullanim:
    python scripts/extract_throws.py
    python scripts/extract_throws.py --window 3 --top 15
"""
import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, "scripts")
from analyze_bvh import read_bvh  # noqa: E402

SRC = Path(r"C:\ufbots_tools\data\remocap_ninjutsu")
DST = Path(r"C:\ufbots_tools\data\throws_bvh")
ROLES = Path("data_prep/ninjutsu_clean.json")


def hip_y(ch, d):
    i = next(k for k, c in enumerate(ch) if c.endswith("Yposition"))
    return d[:, i]


def throw_moment(ch, d, ft) -> float:
    """Atilan kisinin en hizli dustugu an (saniye)."""
    z = hip_y(ch, d)
    vel = -np.diff(z)                      # asagi hiz = pozitif
    w = max(1, int(0.5 / ft))              # 0.5 sn pencere
    if len(vel) < w:
        return len(z) * ft / 2
    roll = np.convolve(vel, np.ones(w) / w, mode="valid")
    return float(roll.argmax() * ft)


def trim_bvh(path: Path, center_s: float, window_s: float, dest: Path):
    """BVH'yi merkez etrafinda keser, basligi korur."""
    lines = path.read_text(errors="replace").splitlines()
    mi = next(i for i, l in enumerate(lines) if l.strip().startswith("MOTION"))
    fi = next(i for i in range(mi, mi + 5) if lines[i].strip().startswith("Frames:"))
    ti = next(i for i in range(mi, mi + 5) if lines[i].strip().startswith("Frame Time:"))
    ft = float(lines[ti].split(":")[1])

    frames = [l for l in lines[ti + 1:] if l.strip()]
    n = len(frames)
    half = int(window_s / ft / 2)
    c = int(center_s / ft)
    a, b = max(0, c - half), min(n, c + half)
    if b - a < 20:
        a, b = 0, min(n, int(window_s / ft))

    cut = frames[a:b]
    dest.write_text("\n".join(lines[:fi] + [f"Frames: {len(cut)}", lines[ti]] + cut) + "\n")
    return len(cut), len(cut) * ft


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--window", type=float, default=4.0)
    ap.add_argument("--top", type=int, default=20, help="en temiz N atis")
    args = ap.parse_args()

    if not ROLES.exists():
        raise SystemExit(f"{ROLES} yok")
    roles = json.loads(ROLES.read_text())

    # en temiz atislar: atilan en dibe inen
    order = sorted(roles.items(), key=lambda kv: kv[1]["atilan_oran"])[: args.top]

    DST.mkdir(parents=True, exist_ok=True)
    print(f"{'shot':<20}{'atan':>6}{'atis_ani':>10}{'sure':>8}")
    print("-" * 46)

    total = 0.0
    for shot, info in order:
        thrower = SRC / f"{shot}_p{info['atan']}.bvh"
        thrown = SRC / f"{shot}_p{info['atilan']}.bvh"
        if not (thrower.exists() and thrown.exists()):
            continue

        # atis anini ATILAN kisiden bul
        ch, d, ft = read_bvh(thrown)
        t = throw_moment(ch, d, ft)

        # ATAN kisinin hareketini o ana gore kes
        dest = DST / f"throw_{shot}.bvh"
        nk, sec = trim_bvh(thrower, t, args.window, dest)
        print(f"{shot:<20}{'p'+info['atan']:>6}{t:>9.1f}s{sec:>7.1f}s")
        total += sec

    print(f"\n{len(order)} atis -> {DST}   toplam {total:.0f} s")


if __name__ == "__main__":
    main()
