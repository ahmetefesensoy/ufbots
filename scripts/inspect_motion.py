"""Indirilen G1 CSV'lerini dogrular ve ozetler.

Egitime gondermeden once veri saglikli mi diye bakmak icin. Bozuk veriyle
egitim baslatmak en pahali hata.

Kullanim:
    python scripts/inspect_motion.py
    python scripts/inspect_motion.py --plot     # eklem egrilerini PNG'ye ciz
"""
import argparse
import glob
from pathlib import Path

import pandas as pd

RAW = Path("data/raw_csv")

# G1 29-DOF; CSV'de ayrica 6 root kanali var
ROOT = ["root_translateX", "root_translateY", "root_translateZ",
        "root_rotateX", "root_rotateY", "root_rotateZ"]


def check(path: Path) -> dict:
    d = pd.read_csv(path)
    joints = [c for c in d.columns if c.endswith("_dof")]
    return {
        "dosya": path.name,
        "frame": len(d),
        "sure_s": round(len(d) / 120, 1),
        "dof": len(joints),
        "nan": int(d.isna().sum().sum()),
        "z_ort_cm": round(d.root_translateZ.mean(), 1),
        "aci_max": round(d[joints].abs().max().max(), 1),
        # Kare arasi sicrama: retarget hatasi varsa burada patlar
        "max_jump_deg": round(d[joints].diff().abs().max().max(), 1),
    }


def main(plot: bool):
    files = sorted(RAW.glob("*.csv"))
    if not files:
        raise SystemExit(f"CSV yok: {RAW}  — once scripts/fetch_motions.py calistir")

    rows = [check(f) for f in files]
    df = pd.DataFrame(rows)
    print(df.to_string(index=False))

    print("\n--- ozet ---")
    print(f"dosya      : {len(df)}")
    print(f"toplam sure: {df.sure_s.sum():.1f} s")
    print(f"NaN        : {df.nan.sum()}")
    print(f"DOF        : {sorted(df.dof.unique())}  (beklenen: 29)")
    print(f"birim      : aci=derece (max {df.aci_max.max():.0f}), konum=cm (z~{df.z_ort_cm.mean():.0f})")

    bad = df[(df.nan > 0) | (df.dof != 29) | (df.max_jump_deg > 30)]
    if bad.empty:
        print("\nOK — tum dosyalar saglikli.")
    else:
        print(f"\nDIKKAT — {len(bad)} dosyada sorun:")
        print(bad.to_string(index=False))

    if plot:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        d = pd.read_csv(files[0])
        arms = [c for c in d.columns if "shoulder" in c or "elbow" in c]
        fig, ax = plt.subplots(2, 1, figsize=(12, 7), sharex=True)
        d[arms].plot(ax=ax[0], lw=.8)
        ax[0].set_title(f"Kol eklemleri — {files[0].name}")
        ax[0].set_ylabel("derece")
        ax[0].legend(fontsize=6, ncol=3)
        d[["root_translateZ"]].plot(ax=ax[1], lw=1, color="k")
        ax[1].set_title("Root yukseklik")
        ax[1].set_ylabel("cm")
        ax[1].set_xlabel("frame")
        plt.tight_layout()
        out = "data/motion_preview.png"
        plt.savefig(out, dpi=110)
        print(f"\nGrafik -> {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--plot", action="store_true")
    main(ap.parse_args().plot)
