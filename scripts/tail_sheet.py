"""Videonun SON karelerinden kontak sayfasi — dusme son anda olur."""
import argparse
from pathlib import Path
import imageio.v2 as iio
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("video"); ap.add_argument("--n", type=int, default=6)
ap.add_argument("--frac", type=float, default=0.80, help="son %% kismi")
ap.add_argument("--scale", type=int, default=4)
a = ap.parse_args()

frames = [f for f in iio.get_reader(a.video)]
idx = np.linspace(len(frames) * a.frac, len(frames) - 1, a.n).astype(int)
s = a.scale
tiles = [frames[i][::s, ::s] for i in idx]
half = len(tiles) // 2
sheet = np.vstack([np.hstack(tiles[:half]), np.hstack(tiles[half:])])
out = Path(a.video).with_name(Path(a.video).stem + "_tail.png")
iio.imwrite(out, sheet)
print(out)
