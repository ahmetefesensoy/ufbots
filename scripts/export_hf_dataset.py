"""HF'ye yuklenebilir veri seti paketi hazirlar.

Form ayri bir "Dataset — Hugging Face" alani istiyor. Cogu katilimci
kullandigi ham veriyi yukleyecek; biz **islenmis + puanlanmis** set
veriyoruz — baskasinin dogrudan kullanabilecegi sey.

Paket icerigi:
    motions/*.csv        G1 29-DOF, BONES-SEED kolon duzeni (derece+cm)
    motions/*.npz        ayni veri numpy (root_pos/root_rot/dof_pos)
    manifest.json        kalite puani, egitim agirligi, kategori
    metrics.csv          tum olcumler tek tabloda
    README.md            HF dataset karti

Kullanim:
    python scripts/export_hf_dataset.py
    python scripts/export_hf_dataset.py --out dist/ufbots-bokator
"""
import argparse
import json
import pickle
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial.transform import Rotation as R

CURATED = Path("C:/ufbots_tools/data/g1_curated")
OUT = Path("dist/ufbots-bokator-g1")

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

CARD = """---
license: other
license_name: bones-seed-and-cmu
task_categories:
- robotics
tags:
- humanoid
- unitree-g1
- motion-capture
- martial-arts
- bokator
size_categories:
- n<1K
---

# ufbots — G1 Bokator Motion Set

**{n} clips · {sec:.0f} seconds · 30 fps · Unitree G1 29-DOF**

Martial-arts motions retargeted to the Unitree G1 humanoid, curated and
quality-scored for SONIC / GR00T-WholeBodyControl fine-tuning.

Inspired by **Bokator** (Khmer battlefield martial art) — specifically
*Chanleak* (flying knee) and *Seah* (horse stance forward drive).
This is an **adaptation, not a reproduction**: Bokator's grappling and
ground techniques are deliberately excluded because the G1 cannot
recover from the floor.

## Pipeline

```
CMU Mocap catalogue
  -> combat motion selection (35 of 239 trials)
  -> AMASS SMPL-X equivalents
  -> joint-aware trimming (peak of the *relevant* joint, not overall motion)
  -> GMR retarget -> G1 29-DOF
  -> Savitzky-Golay smoothing + joint-limit clipping + ground alignment
  -> quality scoring (0-100) + training weights
```

### Why joint-aware trimming matters

Trimming on overall motion energy picks the wrong moment. In an 83-second
clip the real knee strike happens at **54.1 s**, but peak overall motion is
at **36.3 s**. Cutting at the wrong point reduced the knee range from
**120 deg to 15 deg** — the strike was simply not in the clip.

## Format

Each motion is provided twice:

| File | Layout |
|---|---|
| `motions/<name>.csv` | BONES-SEED column order — `Frame`, 6 root channels (deg + cm), 29 `*_dof` columns |
| `motions/<name>.npz` | `root_pos` (m), `root_rot` (wxyz), `dof_pos` (rad) |

The CSV layout is accepted directly by NVIDIA's
`convert_soma_csv_to_motion_lib.py` (flat Bones-SEED CSV mode).

## Quality scoring

`score = upright%(40) + jitter(25) + collapse(20) + amplitude(15)`

- **upright%** — fraction of frames where torso-up z-component > 0.8
- **jitter** — mean second difference of joint angles
- **hop** — hip height / median (1.0 = no airborne phase)

`manifest.json` carries per-clip scores, weights and categories.

## Training weights

Equal sampling drowns the signature moves: 6 flying kicks disappear among
26 ordinary clips. Weights combine quality score with a family multiplier.

| Clip | Weight |
|---|---|
{weights}

## Known limits

- Source is **generic combat mocap**, not authentic Bokator footage
- Elbow strike (*Dum*) is indirect — high elbow angles come from punches
- Grappling/throws are **not included** (G1 cannot stand back up)
- Flying techniques are kinematically valid but may not survive physics training

## Credits

Motion Data by Bones Studio

Source motions: [CMU Graphics Lab Motion Capture Database](http://mocap.cs.cmu.edu/)
(free, no restrictions) via [AMASS](https://amass.is.tue.mpg.de/) SMPL-X.
Retargeting: [GMR](https://github.com/YanjieZe/GMR).
Base-motion mix: [BONES-SEED](https://huggingface.co/datasets/bones-studio/seed).

AMASS and BONES-SEED carry their own licences — this set redistributes only
derived G1 joint trajectories, not the original mocap.
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(CURATED))
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()

    src, out = Path(args.src), Path(args.out)
    mf = src / "manifest.json"
    if not mf.exists():
        raise SystemExit(f"{mf} yok — once curate_dataset.py")

    data = json.loads(mf.read_text(encoding="utf-8"))
    train = [r for r in data["kliplar"] if r["grup"] == "train"]

    if out.exists():
        shutil.rmtree(out)
    (out / "motions").mkdir(parents=True)

    total = 0.0
    for r in train:
        p = src / "train" / f"{r['klip']}.pkl"
        if not p.exists():
            continue
        d = pickle.load(open(p, "rb"))
        pos = np.asarray(d["root_pos"]); quat = np.asarray(d["root_rot"])
        dof = np.asarray(d["dof_pos"]); fps = float(np.asarray(d["fps"]))
        total += len(pos) / fps

        # NPZ
        np.savez(out / "motions" / f"{r['klip']}.npz",
                 root_pos=pos.astype(np.float32),
                 root_rot=quat.astype(np.float32),
                 dof_pos=dof.astype(np.float32),
                 fps=np.float32(fps))

        # CSV (BONES-SEED duzeni)
        eul = R.from_quat(quat[:, [1, 2, 3, 0]]).as_euler("XYZ", degrees=True)
        df = pd.DataFrame({"Frame": np.arange(len(pos))})
        for i, ax in enumerate("XYZ"):
            df[f"root_translate{ax}"] = pos[:, i] * 100
        for i, ax in enumerate("XYZ"):
            df[f"root_rotate{ax}"] = eul[:, i]
        for i, j in enumerate(JOINTS):
            df[f"{j}_dof"] = np.rad2deg(dof[:, i])
        df.to_csv(out / "motions" / f"{r['klip']}.csv", index=False)

    # manifest + metrik tablosu
    (out / "manifest.json").write_text(
        json.dumps({"clips": train}, indent=1, ensure_ascii=False), encoding="utf-8")
    pd.DataFrame(train).to_csv(out / "metrics.csv", index=False)

    sig = sorted([r for r in train if r["agirlik"] >= 1.5], key=lambda r: -r["agirlik"])
    wtab = "\n".join(f"| `{r['klip']}` | {r['agirlik']:.2f} |" for r in sig)
    (out / "README.md").write_text(
        CARD.format(n=len(train), sec=total, weights=wtab), encoding="utf-8")

    mb = sum(f.stat().st_size for f in out.rglob("*")) / 1024 / 1024
    print(f"{len(train)} klip · {total:.0f} s · {mb:.1f} MB -> {out}")
    print("\nYuklemek icin:")
    print(f"  hf upload <kullanici>/ufbots-bokator-g1 {out} --repo-type dataset")


if __name__ == "__main__":
    main()
