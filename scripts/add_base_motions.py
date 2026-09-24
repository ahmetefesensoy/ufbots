"""Taban karisimi ekler — catastrophic forgetting onlemi.

Sadece dovus hareketlerine fine-tune edersek robot yurumeyi, durmayi,
dengede kalmayi unutur. SONIC dokumantasyonu da bunu uyariyor.

Cozum: BONES-SEED'den yurume/denge/durus hareketleri ekleyip karistirmak.
Zaten indirdigimiz shadow_boxing kliplerinin yaninda temel locomotion
hareketleri de cekiliyor.

Oran: literaturde tipik olarak %30-50 taban. Biz %40 aliyoruz —
32 dovus klibi icin ~21 taban klibi.

Kullanim:
    python scripts/add_base_motions.py --list      # ne cekilecek, goster
    python scripts/add_base_motions.py             # indir + retarget kuyruğu
"""
import argparse
import os
from pathlib import Path

import pandas as pd

META = Path("seed_meta/metadata/seed_metadata_v004.parquet")
OUT = Path("data/base_csv")

# Taban icin aranan hareketler — G1'in zaten bildigi, korumak istediklerimiz
WANTED = {
    # Desenler gercek BONES-SEED adlandirmasina gore (explore_seed.py ile dogrulandi)
    "yurume":  (r"^walk_ff_loop_\d+_[LR]_", 8),
    "durus":   (r"^idle_\w+_loop_", 5),
    "donus":   (r"^walk_ff_(start|stop)_(180|270)_[LR]_", 5),
    "denge":   (r"^one_leg_jumping_", 3),
    "comelme": (r"^crouch_ff_loop_", 3),
    "kosu":    (r"^jog_ff_(loop|start)_\d+_[LR]_", 4),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--ratio", type=float, default=0.4, help="taban orani")
    args = ap.parse_args()

    if not META.exists():
        raise SystemExit(f"{META} yok — once metadata indir")
    df = pd.read_parquet(META)
    df = df[~df["is_mirror"]]

    picked = []
    print(f"{'kategori':<12}{'aranan':<36}{'bulunan':>8}")
    print("-" * 60)
    for cat, (pat, n) in WANTED.items():
        hit = df[df["move_name"].str.match(pat, na=False)]
        # kisa ve temiz olanlari sec (3-8 saniye)
        hit = hit[(hit.move_duration_frames > 360) & (hit.move_duration_frames < 960)]
        sel = hit.head(n)
        print(f"{cat:<12}{pat:<36}{len(sel):>8}")
        for _, r in sel.iterrows():
            picked.append({"kategori": cat, "move_name": r["move_name"],
                           "g1_path": r["move_g1_path"],
                           "sure": round(r["move_duration_frames"] / 120, 1)})

    print(f"\ntoplam {len(picked)} taban klibi")
    if picked:
        print(f"tahmini sure: {sum(p['sure'] for p in picked):.0f} s")

    if args.list or not picked:
        for p in picked[:15]:
            print(f"  {p['kategori']:<10} {p['move_name'][:42]:<42} {p['sure']:>5.1f}s")
        if not args.list:
            print("\nHicbiri bulunamadi — desenler BONES-SEED adlandirmasiyla eslesmedi.")
            print("`python scripts/explore_seed.py walk` ile gercek adlari kontrol et.")
        return

    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(picked).to_csv("data_prep/base_motions.csv", index=False)
    print("\n-> data_prep/base_motions.csv")
    print("\nIndirmek icin:")
    print("  $env:HF_TOKEN='<token>'")
    print("  python scripts/fetch_motions.py --pattern '<move_name>'")


if __name__ == "__main__":
    main()
