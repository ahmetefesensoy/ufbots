#!/usr/bin/env bash
# Nebius GPU makinesinde GR00T-WholeBodyControl kurulumu.
# Yerel Windows makinede DEGIL, uzak GPU makinesinde calistirilir.
set -euo pipefail

WBC="${WBC_ROOT:-$HOME/GR00T-WholeBodyControl}"

echo ">>> Git LFS (atlanirsa veri sessizce bozuk gelir)"
git lfs install

if [ ! -d "$WBC" ]; then
  git clone https://github.com/NVlabs/GR00T-WholeBodyControl.git "$WBC"
fi
cd "$WBC"
git lfs pull

echo ">>> Ortam kontrolu"
python check_environment.py

echo ">>> Bagimliliklar"
pip install -e "gear_sonic/[training]"

echo ">>> sonic_release checkpoint indir"
python download_from_hf.py --training

echo
echo "Kurulum tamam."
echo "Isaac Lab (v2.3.2) ayrica kurulmalidir — kuruluysa devam:"
echo "  bash scripts/run_pipeline.sh convert"
