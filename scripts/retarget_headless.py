"""SMPL-X -> Unitree G1 retarget, PENCERE ACMADAN.

GMR'nin kendi scriptleri her klipte zorunlu olarak RobotMotionViewer aciyor:
    robot_motion_viewer = RobotMotionViewer(...)   # smplx_to_robot.py:90

Bu toplu islemede takiliyor — birden fazla surec ayni anda GPU render
baglami acmaya calisinca "gladLoadGL error" veriyor ya da donuyor.

Bu script ayni retarget cekirdegini kullanir ama viewer'i hic olusturmaz.
Cikti formati GMR ile birebir ayni:
    root_pos (N,3) | root_rot (N,4) | dof_pos (N,29) | fps

ASCII yol zorunlu: MuJoCo, yolunda Turkce "İ" olan XML'i acamiyor.

Kullanim:
    python scripts/retarget_headless.py
    python scripts/retarget_headless.py --src <dir> --dst <dir> --robot unitree_g1
"""
import argparse
import pickle
import sys
import time
from pathlib import Path

import numpy as np

DEFAULT_SRC = Path("C:/ufbots_tools/data/amass_trimmed")
DEFAULT_DST = Path("C:/ufbots_tools/data/g1_retargeted")
GMR_DIR = Path("C:/ufbots_tools/GMR")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(DEFAULT_SRC))
    ap.add_argument("--dst", default=str(DEFAULT_DST))
    ap.add_argument("--robot", default="unitree_g1")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--override", action="store_true")
    args = ap.parse_args()

    sys.path.insert(0, str(GMR_DIR))
    from general_motion_retargeting import GeneralMotionRetargeting as GMR
    from general_motion_retargeting.utils.smpl import (
        get_smplx_data_offline_fast, load_smplx_file,
    )

    body_model_path = GMR_DIR / "assets" / "body_models"
    src, dst = Path(args.src), Path(args.dst)
    dst.mkdir(parents=True, exist_ok=True)

    files = sorted(src.glob("*.npz"))
    if not files:
        raise SystemExit(f"NPZ yok: {src}")

    print(f"{len(files)} klip -> {dst}\n")
    ok = skip = fail = 0
    t0 = time.time()

    for i, f in enumerate(files, 1):
        out = dst / f"{f.stem}.pkl"
        if out.exists() and not args.override:
            print(f"[{i}/{len(files)}] {f.stem:<32} atlandi (var)")
            skip += 1
            continue

        print(f"[{i}/{len(files)}] {f.stem:<32} ", end="", flush=True)
        try:
            smplx_data, body_model, smplx_output, height = load_smplx_file(
                str(f), str(body_model_path)
            )
            frames, aligned_fps = get_smplx_data_offline_fast(
                smplx_data, body_model, smplx_output, tgt_fps=args.fps
            )

            # Viewer YOK — sadece retarget cekirdegi
            retarget = GMR(
                actual_human_height=height,
                src_human="smplx",
                tgt_robot=args.robot,
                verbose=False,
            )

            qpos_list = [retarget.retarget(fr) for fr in frames]
            q = np.asarray(qpos_list)

            with open(out, "wb") as fh:
                pickle.dump({
                    "fps": np.array(aligned_fps),
                    "root_pos": q[:, :3],
                    "root_rot": q[:, 3:7],
                    "dof_pos": q[:, 7:],
                }, fh)

            print(f"OK  {len(q)} kare")
            ok += 1
        except Exception as e:
            print(f"HATA: {type(e).__name__}: {str(e)[:70]}")
            fail += 1

    dt = time.time() - t0
    print(f"\ntamam {ok} | atlandi {skip} | hata {fail}   ({dt/60:.1f} dk)")
    print(f"cikti: {dst}")


if __name__ == "__main__":
    main()
