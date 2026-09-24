#!/usr/bin/env bash
# ufbots — SONIC fine-tune hatti (Nebius/GPU makinesinde calistirilir)
#
# Bizim hareketlerimizi sonic_release checkpoint'inden ince ayarlar.
# SIFIRDAN EGITIM DEGIL — NVIDIA 64+ GPU oneriyor, bizim butcemiz yok.
#
# ONKOSUL:
#   1. GR00T-WholeBodyControl kurulu (bash scripts/setup_nebius.sh)
#   2. Isaac Lab v2.3.2 kurulu
#   3. sonic_input/csv/ bu makineye kopyalanmis
#
# Kullanim:
#   bash scripts/train_sonic.sh            # tum adimlar
#   bash scripts/train_sonic.sh convert    # tek adim
set -euo pipefail

WBC="${WBC_ROOT:-$HOME/GR00T-WholeBodyControl}"
OURS="${OURS:-$PWD/sonic_input/csv}"          # ayiklanmis dovus hareketleri
BASE="${BASE:-$PWD/sonic_input/base_csv}"     # taban karisimi (yurume/durus/denge)
SEED="${SEED_DIR:-$PWD/data/bones_seed_g1}"   # taban karisimi (opsiyonel)
OUT="${OUT_DIR:-$PWD/data/motion_lib_ufbots}"

NUM_ENVS="${NUM_ENVS:-4096}"
ITERS="${ITERS:-20000}"
EXP="manager/universal_token/all_modes/sonic_release"

step_convert() {
  echo ">>> 1/4  CSV -> motion_lib PKL"
  cd "$WBC"
  python gear_sonic/data_process/convert_soma_csv_to_motion_lib.py \
      --input "$OURS" \
      --output "$OUT/robot" \
      --fps 30 --fps_source 30 \
      --individual --num_workers 8

  # Filtre: dosya adlarimizda 'cartwheel/handstand/box_jump' yok,
  # o yuzden hicbiri elenmemeli. Yine de calistirip dogruluyoruz.
  # TABAN KARISIMI — catastrophic forgetting onlemi.
  # Sadece dovuse fine-tune edersek robot yurumeyi unutur.
  if [ -d "$BASE" ] && [ "$(ls -A "$BASE" 2>/dev/null)" ]; then
    echo ">>> 1b  Taban hareketleri ekleniyor ($(ls -1 "$BASE" | wc -l) klip)"
    python gear_sonic/data_process/convert_soma_csv_to_motion_lib.py         --input "$BASE" --output "$OUT/robot"         --fps 30 --fps_source 120 --individual --num_workers 8
  else
    echo ">>> 1b  UYARI: taban karisimi yok — robot yurumeyi unutabilir"
  fi

  echo ">>> 2/4  Filtre (bizim adlarda elenecek kelime yok)"
  python gear_sonic/data_process/filter_and_copy_bones_data.py \
      --source "$OUT/robot" \
      --dest "$OUT/robot_filtered" \
      --workers 8
  echo "    girdi : $(ls -1 "$OUT/robot" | wc -l)"
  echo "    kalan : $(ls -1 "$OUT/robot_filtered" | wc -l)"
}

# Egitimden ONCE gozle dogrula — bozuk veriyle GPU saati yakma
step_replay() {
  echo ">>> Replay (ekran gerekir)"
  cd "$WBC"
  python gear_sonic/train_agent_trl.py \
      +exp="$EXP" ++replay=True num_envs=4 headless=False \
      ++manager_env.commands.motion.motion_lib_cfg.motion_file="$OUT/robot_filtered"
}

step_train() {
  echo ">>> 3/4  Fine-tune"
  cd "$WBC"
  # NOT: sadece kendi hareketlerimize fine-tune edersek robot yurumeyi
  # unutur (catastrophic forgetting). Taban karisimi icin BONES-SEED'den
  # yurume/denge hareketleri eklemek onerilir.
  python gear_sonic/train_agent_trl.py \
      +exp="$EXP" \
      +checkpoint=sonic_release/last.pt \
      num_envs="$NUM_ENVS" headless=True \
      ++algo.config.num_learning_iterations="$ITERS" \
      ++manager_env.commands.motion.motion_lib_cfg.motion_file="$OUT/robot_filtered" \
      wandb.wandb_project=ufbots-bokator
  echo "    checkpoint -> $WBC/logs_rl/TRL_G1_Track/"
}

step_eval() {
  local CKPT="${1:?checkpoint yolu gerekli}"
  echo ">>> 4/4  Eval + render"
  cd "$WBC"

  python gear_sonic/eval_agent_trl.py \
      +checkpoint="$CKPT" +headless=True \
      ++eval_callbacks=im_eval ++run_eval_loop=False ++num_envs=128 \
      "+manager_env/terminations=tracking/eval" \
      "++manager_env.commands.motion.motion_lib_cfg.max_unique_motions=512"

  python gear_sonic/eval_agent_trl.py \
      +checkpoint="$CKPT" +headless=True \
      ++eval_callbacks=im_eval ++run_eval_loop=False ++num_envs=8 \
      ++manager_env.config.render_results=True \
      "++manager_env.config.save_rendering_dir=$PWD/results/renders" \
      ++manager_env.config.env_spacing=10.0 \
      "~manager_env/recorders=empty" "+manager_env/recorders=render"
}

step_export() {
  local CKPT="${1:?checkpoint yolu gerekli}"
  echo ">>> ONNX export (submission icin)"
  cd "$WBC"
  python gear_sonic/eval_agent_trl.py \
      +checkpoint="$CKPT" +headless=True ++num_envs=1 \
      +export_onnx_only=true
  echo "    -> $(dirname "$CKPT")/exported/*_g1.onnx"
}

case "${1:-all}" in
  convert) step_convert ;;
  replay)  step_replay ;;
  train)   step_train ;;
  eval)    step_eval "${2:-}" ;;
  export)  step_export "${2:-}" ;;
  all)     step_convert; step_train
           echo "Sonra:  bash $0 eval <ckpt>  &&  bash $0 export <ckpt>" ;;
  *) echo "gecersiz: $1  (convert|replay|train|eval|export|all)"; exit 1 ;;
esac
