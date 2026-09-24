"""Indirilen CMU BVH'lerinden gercek dovus hareketlerini secer.

CMU denekleri karisik icerikli (bir denekte hem yurume hem tekme var).
Trial aciklamalarina bakarak sadece dovus olanlari ayiklar ve
data/combat_bvh/ altina anlamli isimlerle kopyalar.

Dosya adlari ONEMLI: NVIDIA'nin filter_and_copy_bones_data.py scripti
sadece dosya adina bakiyor. "cartwheel", "handstand", "box_jump" gibi
kelimeler iceren adlar elenir — o yuzden temiz ad veriyoruz.

Kullanim:
    python scripts/select_combat.py
    python scripts/select_combat.py --list     # kopyalamadan goster
"""
import argparse
import json
import re
import shutil
from pathlib import Path

SRC = Path("data/cmu_bvh")
DST = Path("data/combat_bvh")
TRIALS = Path("data_prep/cmu_trials.json")

# Dovus sayilan aciklamalar
KEEP = re.compile(r"kick|punch|martial|fight|knee|spin|attack|strike|combat", re.I)
# Bunlar dovus degil ya da G1 icin uygunsuz
DROP = re.compile(r"cartwheel|handstand|soccer|basketball|football|box\b|drink|yawn|"
                  r"pregnant|painful", re.I)

# Aciklamayi kisa, temiz bir etikete cevir (filtreye takilmayacak adlar)
def label(desc: str) -> str:
    d = desc.lower()
    if "jump" in d and "spin" in d:
        return "jump_spin_kick"
    if "jump kick" in d or ("jump" in d and "kick" in d):
        return "jump_kick"          # ucan diz/tekme temeli
    if "spin" in d and "kick" in d:
        return "spin_kick"
    if "knee" in d:
        return "knee_strike"        # muay thai diz
    if "attack" in d or "avoid" in d:
        return "attack_sequence"
    if "punch" in d and "kick" in d:
        return "punch_kick_combo"
    if "front_kick" in d.replace(" ", "_"):
        return "front_kick"
    if "kick" in d:
        return "kick"
    if "punch" in d:
        return "punch"
    if "spin" in d:
        return "spin"
    return "combat"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    if not TRIALS.exists():
        raise SystemExit(f"{TRIALS} yok — once fetch_cmu.py calistir")
    trials = json.loads(TRIALS.read_text(encoding="utf-8"))

    files = sorted(SRC.glob("*.bvh"))
    if not files:
        raise SystemExit(f"{SRC} bos — once fetch_cmu.py calistir")

    picked = []
    for f in files:
        m = re.match(r"cmu_(\d+)_(\d+)_(\d+)\.bvh", f.name)
        if not m:
            continue
        key = f"{int(m.group(1)):03d}_{int(m.group(3)):02d}"
        desc = trials.get(key, "")
        if KEEP.search(desc) and not DROP.search(desc):
            picked.append((key, desc, f, label(desc)))

    print(f"{len(picked)} dovus hareketi / {len(files)} dosya\n")
    counts: dict[str, int] = {}
    for key, desc, f, lab in picked:
        counts[lab] = counts.get(lab, 0) + 1
        dest = DST / f"{lab}_{key}.bvh"
        print(f"  {key}  {lab:<16} {desc[:44]}")
        if not args.list:
            DST.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, dest)

    print("\n--- kategori dagilimi ---")
    for k in sorted(counts, key=lambda x: -counts[x]):
        print(f"  {k:<18} {counts[k]}")

    if not args.list:
        print(f"\nkopyalandi -> {DST}/")
        print("Sonraki: GMR ile G1'e retarget")


if __name__ == "__main__":
    main()
