"""Kaggle'dan inen Kimodo ciktisini duzenli bir klasore acar.

ONEMLI BULGU: Kimodo'nun CSV ciktisi zaten MuJoCo qpos formatinda —
36 kolon, basliksiz, radyan + metre:

    kolon 0-2   root pozisyon (m)
    kolon 3-6   root quaternion (w,x,y,z)
    kolon 7-35  29 eklem acisi (radyan)

MuJoCo Menagerie g1.xml'in nq degeri de 36. Yani donusum GEREKMIYOR,
dosya dogrudan data.qpos'a yazilabilir.

(Model karti "34 eklem" diyor; bu SOMA/NPZ gosterimi icin. CSV ciktisi
29-DOF G1 qpos olarak yaziliyor.)

Bu script sadece zip'i acar, dosyalari <istem>__<ornek>.csv seklinde
duzlestirir ve dogrular.

Kullanim:
    python scripts/import_kimodo.py kimodo_out.zip
    python scripts/import_kimodo.py kimodo_out.zip --outdir data/kimodo_csv
"""
import argparse
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path("data/kimodo_csv")
EXPECTED_COLS = 36


def check(arr: np.ndarray) -> list[str]:
    """Temel saglik kontrolleri; sorun listesi dondurur."""
    issues = []
    if arr.shape[1] != EXPECTED_COLS:
        issues.append(f"kolon {arr.shape[1]} (beklenen {EXPECTED_COLS})")
    if np.isnan(arr).any():
        issues.append(f"{int(np.isnan(arr).sum())} NaN")

    # quaternion normu 1 olmali
    qn = np.linalg.norm(arr[:, 3:7], axis=1)
    if not np.allclose(qn, 1.0, atol=1e-2):
        issues.append(f"quat normu bozuk ({qn.min():.3f}..{qn.max():.3f})")

    # root yuksekligi makul mu (G1 ~0.72 m)
    z = arr[:, 2]
    if z.mean() < 0.3 or z.mean() > 1.2:
        issues.append(f"root yuksekligi tuhaf ({z.mean():.2f} m)")

    # kare arasi sicrama (retarget/uretim hatasi belirtisi)
    jump = np.abs(np.diff(arr[:, 7:], axis=0)).max() if len(arr) > 1 else 0
    if jump > 1.0:  # radyan
        issues.append(f"sicrama {np.rad2deg(jump):.0f} derece")
    return issues


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src", nargs="?", default="kimodo_out.zip")
    ap.add_argument("--outdir", default=str(OUT))
    args = ap.parse_args()

    src = Path(args.src)
    if not src.exists():
        raise SystemExit(f"bulunamadi: {src}")
    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)

    rows = []
    with zipfile.ZipFile(src) as z:
        csvs = [n for n in z.namelist() if n.endswith(".csv")]
        if not csvs:
            raise SystemExit("zip icinde CSV yok")
        print(f"{len(csvs)} CSV bulundu -> {out}/\n")

        for name in sorted(csvs):
            p = Path(name)
            # out/bokator_named/bokator_named_00.csv -> bokator_named__00.csv
            tag = p.parent.name
            stem = p.stem
            idx = stem.replace(f"{tag}_", "") if stem.startswith(tag) else stem
            dest = out / f"{tag}__{idx}.csv"

            arr = pd.read_csv(z.open(name), header=None).to_numpy(dtype=float)
            issues = check(arr)
            # basliksiz kaydet — preview_mujoco dogrudan okuyacak
            pd.DataFrame(arr).to_csv(dest, header=False, index=False)

            rows.append({
                "dosya": dest.name,
                "kare": len(arr),
                "sure_s": round(len(arr) / 30, 1),
                "z_ort": round(float(arr[:, 2].mean()), 2),
                "durum": "OK" if not issues else "; ".join(issues),
            })

    df = pd.DataFrame(rows)
    print(df.to_string(index=False))

    bad = df[df.durum != "OK"]
    print(f"\n{len(df)} dosya, {len(df) - len(bad)} saglikli")
    if len(bad):
        print(f"SORUNLU: {len(bad)}")
    print(f"\nIzlemek icin:\n  python scripts/render_all.py")


if __name__ == "__main__":
    main()
