"""G1 hareketlerini SONIC egitim formatina cevirir.

Iki cikti uretir:

1. **BONES-SEED uyumlu CSV** (derece + cm, baslikli)
   NVIDIA'nin `convert_soma_csv_to_motion_lib.py` scripti bunu
   "mod 4: flat Bones-SEED CSV" olarak kabul ediyor.

2. **Dogrudan motion_lib PKL** (root_trans_offset, pose_aa, dof, root_rot, fps)
   Ara adimi atlamak isteyenler icin.

Girdi: GMR ciktisi PKL (root_pos metre, root_rot quaternion, dof_pos radyan)

Kullanim:
    python scripts/export_for_sonic.py                    # hepsi
    python scripts/export_for_sonic.py --src <dir> --csv-only
"""
import argparse
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial.transform import Rotation as R

# BONES-SEED kolon duzeni — preview_mujoco.py bunu okuyor
ROOT_COLS = ["root_translateX", "root_translateY", "root_translateZ",
             "root_rotateX", "root_rotateY", "root_rotateZ"]

JOINTS = [
    "left_hip_pitch_joint", "left_hip_roll_joint", "left_hip_yaw_joint",
    "left_knee_joint", "left_ankle_pitch_joint", "left_ankle_roll_joint",
    "right_hip_pitch_joint", "right_hip_roll_joint", "right_hip_yaw_joint",
    "right_knee_joint", "right_ankle_pitch_joint", "right_ankle_roll_joint",
    "waist_yaw_joint", "waist_roll_joint", "waist_pitch_joint",
    "left_shoulder_pitch_joint", "left_shoulder_roll_joint", "left_shoulder_yaw_joint",
    "left_elbow_joint", "left_wrist_roll_joint", "left_wrist_pitch_joint",
    "left_wrist_yaw_joint",
    "right_shoulder_pitch_joint", "right_shoulder_roll_joint", "right_shoulder_yaw_joint",
    "right_elbow_joint", "right_wrist_roll_joint", "right_wrist_pitch_joint",
    "right_wrist_yaw_joint",
]

SOURCES = [
    Path("C:/ufbots_tools/data/g1_combos"),   # bokator kombinasyonlari
    Path("C:/ufbots_tools/data/g1_smart"),    # tekil hareketler
]
DST = Path("C:/ufbots_tools/data/sonic_input")


def to_seed_csv(d: dict) -> pd.DataFrame:
    """GMR PKL -> BONES-SEED CSV (derece + cm)."""
    pos = np.asarray(d["root_pos"])
    quat = np.asarray(d["root_rot"])          # w,x,y,z
    dof = np.asarray(d["dof_pos"])            # radyan

    # quaternion -> XYZ euler (derece); scipy x,y,z,w bekler
    eul = R.from_quat(quat[:, [1, 2, 3, 0]]).as_euler("XYZ", degrees=True)

    out = pd.DataFrame()
    out["Frame"] = np.arange(len(pos))
    out["root_translateX"] = pos[:, 0] * 100      # m -> cm
    out["root_translateY"] = pos[:, 1] * 100
    out["root_translateZ"] = pos[:, 2] * 100
    out["root_rotateX"] = eul[:, 0]
    out["root_rotateY"] = eul[:, 1]
    out["root_rotateZ"] = eul[:, 2]
    for i, j in enumerate(JOINTS):
        out[f"{j}_dof"] = np.rad2deg(dof[:, i])
    return out


def to_motion_lib(d: dict) -> dict:
    """GMR PKL -> SONIC motion_lib PKL."""
    pos = np.asarray(d["root_pos"], dtype=np.float32)
    quat = np.asarray(d["root_rot"], dtype=np.float32)
    dof = np.asarray(d["dof_pos"], dtype=np.float32)
    fps = float(np.asarray(d["fps"]))

    # root_rot: motion_lib x,y,z,w bekliyor (GMR w,x,y,z veriyor)
    root_rot = quat[:, [1, 2, 3, 0]]
    # pose_aa: eksen-aci gosterimi (N, J, 3) — kok + eklemler
    aa_root = R.from_quat(root_rot).as_rotvec().astype(np.float32)
    pose_aa = np.concatenate(
        [aa_root[:, None, :], np.zeros((len(dof), len(JOINTS), 3), np.float32)], axis=1
    )

    return {
        "root_trans_offset": pos,
        "root_rot": root_rot,
        "dof": dof,
        "pose_aa": pose_aa,
        "fps": fps,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", nargs="+", default=[str(p) for p in SOURCES])
    ap.add_argument("--dst", default=str(DST))
    ap.add_argument("--csv-only", action="store_true")
    ap.add_argument("--pkl-only", action="store_true")
    args = ap.parse_args()

    dst = Path(args.dst)
    (dst / "csv").mkdir(parents=True, exist_ok=True)
    (dst / "motion_lib").mkdir(parents=True, exist_ok=True)

    files = []
    for s in args.src:
        files += sorted(Path(s).glob("*.pkl"))
    if not files:
        raise SystemExit("PKL bulunamadi")

    print(f"{len(files)} hareket -> {dst}\n")
    total = 0.0
    for f in files:
        d = pickle.load(open(f, "rb"))
        n = len(d["root_pos"])
        fps = float(np.asarray(d["fps"]))
        total += n / fps

        if not args.pkl_only:
            to_seed_csv(d).to_csv(dst / "csv" / f"{f.stem}.csv", index=False)
        if not args.csv_only:
            with open(dst / "motion_lib" / f"{f.stem}.pkl", "wb") as fh:
                pickle.dump(to_motion_lib(d), fh)

        print(f"  {f.stem:<26} {n:4d} kare  {n/fps:4.1f}s")

    print(f"\ntoplam {total:.0f} s")
    print(f"\nCSV      : {dst/'csv'}       (NVIDIA convert scripti icin)")
    print(f"motion_lib: {dst/'motion_lib'} (dogrudan egitim icin)")


if __name__ == "__main__":
    main()
