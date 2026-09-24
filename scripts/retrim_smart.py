"""Klipleri HAREKETIN TURUNE gore keser.

Onceki trim_bvh.py genel eklem hareketliligine bakiyordu. Bu yanlisti:
knee_strike_86_06'da gercek diz vurusu 54.1s'de (109 derece) ama
genel hareket tepesi 36.3s'deydi — yanlis yeri kestik, diz vurusu kacti.

Bu script her kategori icin DOGRU eklemi izler:
    knee_strike  -> diz acisi
    jump_*       -> kalca yuksekligi (havada faz)
    kick/front_* -> kalca pitch (bacak savurma)
    punch        -> dirsek/omuz
    spin         -> govde yaw

Kullanim:
    python scripts/retrim_smart.py
    python scripts/retrim_smart.py --window 3
"""
import argparse
import re
from pathlib import Path

import numpy as np

SRC = Path("data/amass_combat")          # kesilmemis orijinaller
DST = Path("C:/ufbots_tools/data/amass_smart")

# SMPL-X pose_body: 21 eklem x 3 axis-angle (pelvis haric, 0-tabanli)
J = {
    "L_hip": 0, "R_hip": 1, "spine1": 2,
    "L_knee": 3, "R_knee": 4, "spine2": 5,
    "L_ankle": 6, "R_ankle": 7, "spine3": 8,
    "L_foot": 9, "R_foot": 10, "neck": 11,
    "L_collar": 12, "R_collar": 13, "head": 14,
    "L_shoulder": 15, "R_shoulder": 16,
    "L_elbow": 17, "R_elbow": 18,
    "L_wrist": 19, "R_wrist": 20,
}

TIME_KEYS = ["trans", "poses", "root_orient", "pose_body",
             "pose_hand", "pose_jaw", "pose_eye", "dmpls"]


def signal_for(tag: str, pb: np.ndarray, trans: np.ndarray) -> tuple[np.ndarray, str]:
    """Kategoriye gore izlenecek sinyali dondurur."""
    def ang(*names):
        idx = [J[n] for n in names]
        return np.rad2deg(np.linalg.norm(pb[:, idx, :], axis=2)).max(axis=1)

    if tag.startswith("knee_strike"):
        return ang("L_knee", "R_knee"), "diz acisi"
    if tag.startswith(("jump_kick", "jump_spin")):
        z = trans[:, 2]
        return z - np.median(z), "kalca yuksekligi"
    if tag.startswith(("kick", "front_kick")):
        return ang("L_hip", "R_hip"), "kalca pitch"
    if tag.startswith("punch"):
        return ang("L_elbow", "R_elbow", "L_shoulder", "R_shoulder"), "kol"
    if tag.startswith("spin"):
        return ang("spine1", "spine2", "spine3"), "govde"
    # karma / bilinmeyen: tum eklemlerin hizi
    d = np.abs(np.diff(pb.reshape(len(pb), -1), axis=0)).mean(axis=1)
    return np.r_[d, d[-1]], "genel hareket"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--window", type=float, default=4.0)
    ap.add_argument("--src", default=str(SRC))
    ap.add_argument("--dst", default=str(DST))
    args = ap.parse_args()

    src, dst = Path(args.src), Path(args.dst)
    dst.mkdir(parents=True, exist_ok=True)

    files = sorted(src.glob("*.npz"))
    if not files:
        raise SystemExit(f"NPZ yok: {src}")

    print(f"{'klip':<30}{'izlenen':<18}{'tepe':>8}{'eski':>8}{'sure':>8}")
    print("-" * 74)

    for f in files:
        z = dict(np.load(f, allow_pickle=True))
        fps = float(z.get("mocap_frame_rate", 120.0))
        pb = z["pose_body"].reshape(len(z["pose_body"]), 21, 3)
        n = len(pb)

        tag = re.sub(r"_\d+_\d+$", "", f.stem)
        sig, what = signal_for(tag, pb, z["trans"])

        # 1 sn kayan pencere tepesi
        w = max(1, int(fps))
        roll = np.convolve(sig, np.ones(w) / w, mode="valid") if len(sig) >= w else sig
        peak_i = int(roll.argmax())
        peak_s = peak_i / fps

        half = int(args.window * fps / 2)
        a, b = max(0, peak_i - half), min(n, peak_i + half)
        if b - a < 30:
            a, b = 0, min(n, int(args.window * fps))

        for k in TIME_KEYS:
            if k in z and hasattr(z[k], "shape") and z[k].ndim >= 1 and len(z[k]) == n:
                z[k] = z[k][a:b]
        z["mocap_time_length"] = np.array((b - a) / fps)
        np.savez(dst / f.name, **z)

        print(f"{f.stem:<30}{what:<18}{peak_s:7.1f}s{n/fps:7.0f}s{(b-a)/fps:7.1f}s")

    tot = sum(float(np.load(p, allow_pickle=True)["mocap_time_length"]) for p in dst.glob("*.npz"))
    print(f"\n{len(files)} klip -> {dst}   toplam {tot:.0f} s")


if __name__ == "__main__":
    main()
