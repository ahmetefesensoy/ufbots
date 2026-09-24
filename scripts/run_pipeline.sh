#!/usr/bin/env bash
# Shadow boxing deneme hatti — Nebius GPU makinesinde calistirilir.
#
# Bu bir DENEME kosusudur: amac borunun ucdan uca calistigini gormek,
# yarisma kalitesinde politika uretmek degil.
#
# Kullanim:
#   bash scripts/run_pipeline.sh            # tum adimlar
#   bash scripts/run_pipeline.sh convert    # tek adim
set -euo pipefail

WBC="${WBC_ROOT:-$HOME/GR00T-WholeBodyControl}"
PROJ="${PROJ_ROOT:-$PWD}"
RAW="$PROJ/data/raw_csv"
OUT="$PROJ/data/motion_lib"
EXP="manager/universal_token/all_modes/sonic_release"

# Deneme olcegi — gercek egitimde num_envs=4096, iterasyon sinirsiz
NUM_ENVS="${NUM_ENVS:-1024}"
ITERS="${ITERS:-2000}"

step_convert() {
  echo ">>> 1/4  CSV -> motion_lib PKL"
  cd "$WBC"
  python gear_sonic/data_process/convert_soma_csv_to_motion_lib.py \
      --input "$RAW" \
      --output "$OUT/robot" \
      --fps 30 --fps_source 120 \
      --individual --num_workers 8

  echo ">>> 2/4  Filtre (G1'in yapamayacagi hareketleri ele)"
  python gear_sonic/data_process/filter_and_copy_bones_data.py \
      --source "$OUT/robot" \
      --dest "$OUT/robot_filtered" \
      --workers 8
  echo "    kalan: $(ls -1 "$OUT/robot_filtered" | wc -l) dosya"
}

# Egitimden once referans hareketi gozle dogrula (headless=False, ekran gerekir)
step_replay() {
  echo ">>> Replay — referans hareketi izle"
  cd "$WBC"
  python gear_sonic/train_agent_trl.py \
      +exp="$EXP" ++replay=True num_envs=4 headless=False \
      ++manager_env.commands.motion.motion_lib_cfg.motion_file="$OUT/robot_filtered"
}

step_train() {
  echo ">>> 3/4  Fine-tune (sonic_release checkpoint'inden)"
  cd "$WBC"
  python gear_sonic/train_agent_trl.py \
      +exp="$EXP" \
      +checkpoint=sonic_release/last.pt \
      num_envs="$NUM_ENVS" headless=True \
      ++algo.config.num_learning_iterations="$ITERS" \
      ++manager_env.commands.motion.motion_lib_cfg.motion_file="$OUT/robot_filtered" \
      wandb.wandb_project=ufbots-shadowboxing
  echo "    checkpoint -> $WBC/logs_rl/TRL_G1_Track/"
}

# $1 = checkpoint yolu
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
      "++manager_env.config.save_rendering_dir=$PROJ/results/renders" \
      ++manager_env.config.env_spacing=10.0 \
      "~manager_env/recorders=empty" "+manager_env/recorders=render"
  echo "    video -> $PROJ/results/renders/"
}

step_export() {
  local CKPT="${1:?checkpoint yolu gerekli}"
  echo ">>> ONNX export"
  cd "$WBC"
  python gear_sonic/eval_agent_trl.py \
      +checkpoint="$CKPT" +headless=True ++num_envs=1 \
      +export_onnx_only=true
  echo "    onnx -> $(dirname "$CKPT")/exported/"
}

case "${1:-all}" in
  convert) step_convert ;;
  replay)  step_replay ;;
  train)   step_train ;;
  eval)    step_eval "${2:-}" ;;
  export)  step_export "${2:-}" ;;
  all)     step_convert; step_train
           echo "Egitim bitti. Sonra:  bash $0 eval <ckpt>  &&  bash $0 export <ckpt>" ;;
  *) echo "gecersiz adim: $1  (convert|replay|train|eval|export|all)"; exit 1 ;;
esac
