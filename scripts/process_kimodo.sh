#!/usr/bin/env bash
# Kaggle ciktisini bastan sona isler: cevir -> karsilastir -> render.
# Kullanim: bash scripts/process_kimodo.sh <zip yolu>
set -euo pipefail
ZIP="${1:-kimodo_out.zip}"
[ -f "$ZIP" ] || { echo "zip yok: $ZIP"; exit 1; }

echo ">>> 1/3  34 -> 29 eklem donusumu"
python scripts/import_kimodo.py "$ZIP"

echo; echo ">>> 2/3  isimle vs tarifle karsilastirmasi"
python scripts/compare_prompts.py

echo; echo ">>> 3/3  G1'de render + kontak sayfalari"
python scripts/render_all.py

echo; echo "Bitti. Sonuclar: results/kimodo/"
