"""AMASS CMU arsivinden sadece sectigimiz dovus kliplerini cikarir.

Arsiv 3.15 GB ve ~2000 dosya; hepsini acmaya gerek yok.
data/combat_trimmed/ icindeki 29 klibin SMPL-X karsiliklarini bulur.

Dosya adi eslesmesi:
    combat_trimmed/knee_strike_086_06.bvh  ->  CMU/86/86_06_stageii.npz

Kullanim:
    python scripts/extract_amass.py
    python scripts/extract_amass.py --archive <yol> --all
"""
import argparse
import re
import tarfile
from pathlib import Path

DEFAULT_ARCHIVE = Path.home() / "Downloads" / "CMU.tar.bz2"
SELECTED = Path("data/combat_trimmed")
OUT = Path("data/amass_combat")


def wanted_keys() -> dict[str, str]:
    """combat_trimmed dosyalarindan (denek, trial) -> etiket haritasi."""
    keys = {}
    for f in sorted(SELECTED.glob("*.bvh")):
        m = re.search(r"_(\d{3})_(\d{2})\.bvh$", f.name)
        if not m:
            continue
        subj, trial = int(m.group(1)), m.group(2)
        label = f.name[: m.start()]           # knee_strike, jump_kick, ...
        # AMASS klasoru sifirsiz: CMU/86/86_06_stageii.npz
        keys[f"{subj}_{trial}"] = label
    return keys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", default=str(DEFAULT_ARCHIVE))
    ap.add_argument("--outdir", default=str(OUT))
    ap.add_argument("--all", action="store_true", help="tum CMU'yu cikar (3 GB)")
    args = ap.parse_args()

    arc = Path(args.archive)
    if not arc.exists():
        raise SystemExit(f"arsiv yok: {arc}")

    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)

    want = wanted_keys()
    print(f"aranan: {len(want)} klip\n")

    found, shapes = 0, 0
    with tarfile.open(arc, "r:bz2") as t:
        for m in t:
            if not m.name.endswith(".npz"):
                continue

            # shape dosyalari (neutral_stagei.npz) — retarget icin gerekli
            if m.name.endswith("_stagei.npz"):
                if not args.all:
                    continue
                dest = out / "shapes" / Path(m.name).name
                dest.parent.mkdir(exist_ok=True)
                dest.write_bytes(t.extractfile(m).read())
                shapes += 1
                continue

            mm = re.search(r"/(\d+)/(\d+)_(\d+)_stageii\.npz$", m.name)
            if not mm:
                continue
            key = f"{int(mm.group(2))}_{mm.group(3)}"

            if not args.all and key not in want:
                continue

            label = want.get(key, "other")
            dest = out / f"{label}_{key}.npz"
            dest.write_bytes(t.extractfile(m).read())
            found += 1
            print(f"  {dest.name}  ({dest.stat().st_size/1024:.0f} KB)")

    print(f"\ncikarilan: {found} klip" + (f", {shapes} shape" if shapes else ""))
    eksik = [k for k in want if not list(out.glob(f"*_{k}.npz"))]
    if eksik:
        print(f"BULUNAMAYAN ({len(eksik)}): {', '.join(sorted(eksik))}")
    print(f"konum: {out}/")


if __name__ == "__main__":
    main()
