#!/usr/bin/env bash
# AMASS SMPL-X kliplerini tek tek G1'e retarget eder.
#
# Neden toplu script degil: smplx_to_robot_dataset.py bizde hic cikti
# uretmeden timeout'a dusuyor (muhtemelen pencere acmaya calisiyor).
# Tek klip komutu ise sorunsuz calisiyor — onu donguye aliyoruz.
#
# ASCII yol zorunlu: MuJoCo, yolunda Turkce "İ" olan XML'i acamiyor.
set -uo pipefail

GMR="${GMR_DIR:-/c/ufbots_tools/GMR}"
SRC="${SRC_DIR:-/c/ufbots_tools/data/amass_trimmed}"
DST="${DST_DIR:-/c/ufbots_tools/data/g1_retargeted}"

mkdir -p "$DST"
cd "$GMR"

total=$(ls "$SRC"/*.npz 2>/dev/null | wc -l)
i=0; ok=0; fail=0

for f in "$SRC"/*.npz; do
  i=$((i+1))
  name=$(basename "$f" .npz)
  out="$DST/$name.pkl"

  if [ -f "$out" ]; then
    echo "[$i/$total] $name — zaten var, atlandi"
    ok=$((ok+1)); continue
  fi

  printf "[%d/%d] %-32s " "$i" "$total" "$name"
  if PYTHONIOENCODING=utf-8 PYTHONUTF8=1 timeout 300 \
     python scripts/smplx_to_robot.py \
       --smplx_file "$f" --robot unitree_g1 --save_path "$out" \
       >/dev/null 2>&1 && [ -f "$out" ]; then
    echo "OK"
    ok=$((ok+1))
  else
    echo "HATA"
    fail=$((fail+1))
  fi
done

echo
echo "tamam: $ok/$total   hata: $fail"
echo "cikti: $DST"
