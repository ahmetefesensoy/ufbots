"""GMR'nin urettigi G1 PKL'lerini MuJoCo'da oynatir ve analiz eder.

GMR cikti formati:
    root_pos  (N, 3)    metre
    root_rot  (N, 4)    quaternion (w,x,y,z)
    dof_pos   (N, 29)   radyan
    fps       ()

Bu tam MuJoCo qpos duzeni (3 + 4 + 29 = 36), donusum gerekmez.

Kullanim:
    python scripts/preview_g1_pkl.py --list              # metrik tablosu
    python scripts/preview_g1_pkl.py --render            # hepsini videoya al
    python scripts/preview_g1_pkl.py --pkl <yol> --video out.mp4
"""
import argparse
import pickle
from pathlib import Path

import numpy as np

SRC = Path("C:/ufbots_tools/data/g1_retargeted")
MODEL = "assets/unitree_g1/scene_hd.xml"
OUT = Path("results/g1_retargeted")


def load(p: Path):
    d = pickle.load(open(p, "rb"))
    n = len(d["root_pos"])
    qpos = np.zeros((n, 36))
    qpos[:, 0:3] = d["root_pos"]
    qpos[:, 3:7] = d["root_rot"]
    qpos[:, 7:] = d["dof_pos"]
    return qpos, float(np.asarray(d["fps"]))


def metrics(qpos: np.ndarray, fps: float) -> dict:
    z = qpos[:, 2]
    j = qpos[:, 7:]
    d = np.abs(np.diff(j, axis=0)) if len(j) > 1 else np.zeros((1, 29))
    return {
        "kare": len(qpos),
        "sure_s": round(len(qpos) / fps, 1),
        "z_ort": round(float(z.mean()), 2),
        "z_min": round(float(z.min()), 2),
        "z_max": round(float(z.max()), 2),
        # havada faz: kalca medyanin ustune ne kadar cikmis
        "sicrama": round(float(z.max() / (np.median(z) + 1e-9)), 2),
        "hareket": round(float(np.rad2deg(d.mean())), 2),
        "tepe": round(float(np.rad2deg(d.mean(axis=1).max())), 1),
    }


def render(qpos: np.ndarray, fps: float, out: Path, frames: int | None = None):
    import imageio.v2 as imageio
    import mujoco

    model = mujoco.MjModel.from_xml_path(MODEL)
    data = mujoco.MjData(model)
    if qpos.shape[1] != model.nq:
        raise SystemExit(f"kolon {qpos.shape[1]} != model nq {model.nq}")

    step = max(1, int(fps // 30))
    q = qpos[::step]
    if frames:
        q = q[:frames]

    r = mujoco.Renderer(model, height=720, width=1280)
    cam = mujoco.MjvCamera()
    mujoco.mjv_defaultCamera(cam)
    cam.distance, cam.elevation, cam.azimuth = 2.6, -10, 150

    out.parent.mkdir(parents=True, exist_ok=True)
    with imageio.get_writer(out, fps=30, macro_block_size=1) as w:
        for fr in q:
            data.qpos[:] = fr
            mujoco.mj_forward(model, data)
            cam.lookat[:2] = data.qpos[:2]
            cam.lookat[2] = 0.8
            r.update_scene(data, camera=cam)
            w.append_data(r.render())
    return len(q)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(SRC))
    ap.add_argument("--pkl", help="tek dosya")
    ap.add_argument("--video", help="tek dosya icin cikti mp4")
    ap.add_argument("--render", action="store_true", help="hepsini videoya al")
    ap.add_argument("--frames", type=int)
    args = ap.parse_args()

    if args.pkl:
        q, fps = load(Path(args.pkl))
        print(metrics(q, fps))
        if args.video:
            n = render(q, fps, Path(args.video), args.frames)
            print(f"video -> {args.video}  ({n} kare)")
        return

    files = sorted(Path(args.dir).glob("*.pkl"))
    if not files:
        raise SystemExit(f"PKL yok: {args.dir}")

    import pandas as pd
    rows = []
    for f in files:
        try:
            q, fps = load(f)
            rows.append({"dosya": f.stem, **metrics(q, fps)})
        except Exception as e:
            print(f"  HATA {f.name}: {type(e).__name__}")

    df = pd.DataFrame(rows).sort_values("sicrama", ascending=False)
    print(df.to_string(index=False))
    print(f"\n{len(df)} klip, toplam {df.sure_s.sum():.0f} s")

    if args.render:
        OUT.mkdir(parents=True, exist_ok=True)
        for f in files:
            q, fps = load(f)
            mp4 = OUT / f"{f.stem}.mp4"
            print(f"  render {f.stem}")
            render(q, fps, mp4, args.frames)
        print(f"\nvideolar -> {OUT}/")


if __name__ == "__main__":
    main()
