"""Render edilmis mp4'ten kontak sayfasi (PNG) uretir.

Videoyu izlemeden hareketin dogru oldugunu hizlica gormek icin.

Kullanim:
    python scripts/contact_sheet.py results/preview_shadowboxing.mp4
    python scripts/contact_sheet.py <mp4> --cols 4 --rows 2 -o out.png
"""
import argparse
from pathlib import Path

import imageio.v2 as iio
import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--cols", type=int, default=3)
    ap.add_argument("--rows", type=int, default=2)
    ap.add_argument("--scale", type=int, default=3, help="kucultme faktoru")
    ap.add_argument("-o", "--out")
    args = ap.parse_args()

    src = Path(args.video)
    if not src.exists():
        raise SystemExit(f"video yok: {src}")

    frames = [f for f in iio.get_reader(src)]
    n = args.cols * args.rows
    # bas ve sondaki durgun kareleri atla, ortadan esit aralikli sec
    idx = np.linspace(len(frames) * 0.15, len(frames) * 0.85, n).astype(int)

    s = args.scale
    tiles = [frames[i][::s, ::s] for i in idx]
    sheet = np.vstack([np.hstack(tiles[r * args.cols:(r + 1) * args.cols])
                       for r in range(args.rows)])

    out = Path(args.out) if args.out else src.with_name(src.stem + "_sheet.png")
    iio.imwrite(out, sheet)
    print(f"{len(frames)} kare ({len(frames)/30:.1f}s) -> {out}  {sheet.shape[1]}x{sheet.shape[0]}")


if __name__ == "__main__":
    main()
