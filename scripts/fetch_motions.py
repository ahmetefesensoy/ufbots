"""g1.tar.gz'den sadece istenen motion'lari cikarir.

Arsiv 21.89 GB; tamamini indirmek yerine stream ederek okur ve aranan
dosyalar bulununca durur. Sadece deneme icin birkac motion cekmeye uygun.

Kullanim:
    python scripts/fetch_motions.py                    # shadow_boxing (varsayilan)
    python scripts/fetch_motions.py --pattern scissor_kick
    python scripts/fetch_motions.py --no-mirror        # mirror kopyalari atla
"""
import argparse
import os
import sys
import tarfile
from pathlib import Path

import pandas as pd
import requests
from huggingface_hub import get_hf_file_metadata, hf_hub_url

REPO = "bones-studio/seed"
ARCHIVE = "g1.tar.gz"
META = Path("seed_meta/metadata/seed_metadata_v004.parquet")
OUT = Path("data/raw_csv")


def wanted_paths(pattern: str, include_mirror: bool) -> set[str]:
    """Metadata'dan desene uyan motion'larin arsiv ici yollarini toplar."""
    df = pd.read_parquet(META)
    sel = df[df["move_name"].str.contains(pattern, na=False, regex=True)]
    if not include_mirror:
        sel = sel[~sel["is_mirror"]]
    if sel.empty:
        sys.exit(f"'{pattern}' ile eslesen motion yok.")
    print(f"Hedef: {len(sel)} motion  (pattern='{pattern}', mirror={'dahil' if include_mirror else 'haric'})")
    return set(sel["move_g1_path"])


def stream_extract(targets: set[str], token: str) -> int:
    """Arsivi stream ederek hedef dosyalari cikarir; hepsi bulununca durur."""
    url = hf_hub_url(REPO, ARCHIVE, repo_type="dataset")
    meta = get_hf_file_metadata(url, token=token)
    print(f"Arsiv: {meta.size / 1024**3:.2f} GB  — stream baslıyor\n")

    OUT.mkdir(parents=True, exist_ok=True)
    remaining = set(targets)
    found = 0

    with requests.get(meta.location, stream=True, timeout=60) as r:
        r.raise_for_status()
        # gzip akisi sirali okunur; "r|gz" seek gerektirmez
        with tarfile.open(fileobj=r.raw, mode="r|gz") as tar:
            for member in tar:
                if not remaining:
                    break
                if member.name not in remaining:
                    continue
                f = tar.extractfile(member)
                if f is None:
                    continue
                dest = OUT / Path(member.name).name
                dest.write_bytes(f.read())
                remaining.discard(member.name)
                found += 1
                print(f"  [{found}/{len(targets)}] {dest.name}  ({member.size/1024:.0f} KB)")

    if remaining:
        print(f"\nUyari: {len(remaining)} dosya bulunamadi:")
        for p in sorted(remaining)[:5]:
            print("   ", p)
    return found


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pattern", default="shadow_boxing",
                    help="move_name icinde aranacak regex (varsayilan: shadow_boxing)")
    ap.add_argument("--no-mirror", action="store_true", help="mirror kopyalari atla")
    args = ap.parse_args()

    tok = os.environ.get("HF_TOKEN")
    if not tok:
        sys.exit("HF_TOKEN tanimli degil.")
    if not META.exists():
        sys.exit(f"Metadata yok: {META}")

    n = stream_extract(wanted_paths(args.pattern, not args.no_mirror), tok)
    print(f"\nTamam: {n} dosya -> {OUT}/")
