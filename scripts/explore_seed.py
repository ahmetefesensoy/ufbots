"""BONES-SEED metadata kesif araci.

Kullanim:
    python scripts/explore_seed.py                 # genel ozet
    python scripts/explore_seed.py kick punch      # terim arama
"""
import sys
from pathlib import Path

import pandas as pd

META = Path("seed_meta/metadata/seed_metadata_v004.parquet")

DESC_COLS = [
    "move_name", "content_name",
    "content_natural_desc_1", "content_natural_desc_2",
    "content_natural_desc_3", "content_natural_desc_4",
    "content_technical_description",
    "content_short_description", "content_short_description_2",
]


def load():
    if not META.exists():
        sys.exit(f"Metadata yok: {META}\nOnce indir: hf download bones-studio/seed "
                 f"--repo-type dataset --include 'metadata/*' --local-dir ./seed_meta")
    df = pd.read_parquet(META)
    # Aramalarda tum aciklamalari tek metinde birlestir
    df["_blob"] = df[DESC_COLS].fillna("").agg(" ".join, axis=1).str.lower()
    return df


def summary(df):
    print(f"Toplam motion : {len(df):,}")
    print(f"Benzersiz     : {(~df['is_mirror']).sum():,}  (yarisi mirror kopyasi)")
    print(f"Toplam sure   : {df['move_duration_frames'].sum() / 120 / 3600:.1f} saat @120fps")
    print("\n=== PACKAGE ===")
    print(df["package"].value_counts().to_string())
    print("\n=== CATEGORY ===")
    print(df["category"].value_counts().to_string())


def search(df, terms):
    for t in terms:
        hit = df[df["_blob"].str.contains(t.lower(), regex=False) & ~df["is_mirror"]]
        print(f"\n=== '{t}' -> {len(hit)} benzersiz motion ===")
        if hit.empty:
            continue
        # Varyasyon son eklerini atip hareket ailelerini grupla
        fam = hit["move_name"].str.replace(r"_\d+__A\d+.*$", "", regex=True)
        print(fam.value_counts().head(15).to_string())


if __name__ == "__main__":
    df = load()
    if len(sys.argv) > 1:
        search(df, sys.argv[1:])
    else:
        summary(df)
