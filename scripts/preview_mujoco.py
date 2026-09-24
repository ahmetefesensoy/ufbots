"""G1 CSV motion'ini MuJoCo'da oynatir — GPU gerekmez.

Kinematik onizleme: eklem acilari dogrudan modele yazilir, fizik
simulasyonu KOSMAZ. Amac "veri G1'de mantikli duruyor mu" sorusunu
egitim baslamadan, bedava yanitlamak.

Kullanim:
    python scripts/preview_mujoco.py                    # interaktif pencere
    python scripts/preview_mujoco.py --video out.mp4    # video kaydet
    python scripts/preview_mujoco.py --csv <yol> --frames 300
"""
import argparse
from pathlib import Path

import mujoco
import numpy as np
import pandas as pd

MODEL = "assets/unitree_g1/scene_hd.xml"
DEFAULT_CSV = "data/raw_csv/shadow_boxing_R_001__A359.csv"

CM_TO_M = 0.01
SRC_FPS = 120


def load_frames(csv_path: Path, model: mujoco.MjModel) -> np.ndarray:
    """CSV -> qpos dizisi.

    Iki format desteklenir:
      1) BONES-SEED : baslikli, derece + cm, Frame + 6 root + 29 dof
      2) Kimodo     : basliksiz, radyan + m, zaten MuJoCo qpos (36 kolon)
    """
    head = pd.read_csv(csv_path, nrows=1, header=None)
    # Ilk hucre sayiya cevrilebiliyorsa baslik yok -> Kimodo qpos
    try:
        float(head.iloc[0, 0])
        arr = pd.read_csv(csv_path, header=None).to_numpy(dtype=float)
        if arr.shape[1] != model.nq:
            raise SystemExit(f"{csv_path.name}: {arr.shape[1]} kolon, model nq={model.nq}")
        return arr
    except (ValueError, TypeError):
        pass  # baslikli -> SEED formati, asagida islenir

    d = pd.read_csv(csv_path)
    joint_cols = [c for c in d.columns if c.endswith("_dof")]

    # CSV kolon sirasi modelin qpos sirasiyla ayni olmayabilir; isimle esle
    order = []
    for c in joint_cols:
        jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, c.replace("_dof", ""))
        if jid < 0:
            raise SystemExit(f"Eklem modelde yok: {c}")
        order.append((model.jnt_qposadr[jid], c))

    n = len(d)
    qpos = np.zeros((n, model.nq))
    qpos[:, 0] = d.root_translateX * CM_TO_M
    qpos[:, 1] = d.root_translateY * CM_TO_M
    qpos[:, 2] = d.root_translateZ * CM_TO_M

    # root donusu: XYZ euler (derece) -> quaternion (w,x,y,z)
    eul = np.deg2rad(d[["root_rotateX", "root_rotateY", "root_rotateZ"]].to_numpy())
    cx, cy, cz = np.cos(eul[:, 0] / 2), np.cos(eul[:, 1] / 2), np.cos(eul[:, 2] / 2)
    sx, sy, sz = np.sin(eul[:, 0] / 2), np.sin(eul[:, 1] / 2), np.sin(eul[:, 2] / 2)
    qpos[:, 3] = cx * cy * cz + sx * sy * sz
    qpos[:, 4] = sx * cy * cz - cx * sy * sz
    qpos[:, 5] = cx * sy * cz + sx * cy * sz
    qpos[:, 6] = cx * cy * sz - sx * sy * cz

    for adr, col in order:
        qpos[:, adr] = np.deg2rad(d[col].to_numpy())
    return qpos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=DEFAULT_CSV)
    ap.add_argument("--video", help="mp4 olarak kaydet (pencere acmaz)")
    ap.add_argument("--fps", type=int, default=30, help="cikti fps")
    ap.add_argument("--frames", type=int, help="ilk N kare ile sinirla")
    args = ap.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        raise SystemExit(f"CSV yok: {csv_path}")

    model = mujoco.MjModel.from_xml_path(MODEL)
    data = mujoco.MjData(model)
    qpos = load_frames(csv_path, model)

    step = max(1, SRC_FPS // args.fps)
    qpos = qpos[::step]
    if args.frames:
        qpos = qpos[: args.frames]

    print(f"{csv_path.name}: {len(qpos)} kare @ {args.fps} fps ({len(qpos)/args.fps:.1f} s)")

    if args.video:
        import imageio.v2 as imageio

        renderer = mujoco.Renderer(model, height=720, width=1280)
        cam = mujoco.MjvCamera()
        mujoco.mjv_defaultCamera(cam)
        cam.distance, cam.elevation, cam.azimuth = 2.2, -8, 150
        cam.lookat[:] = [0, 0, 0.8]

        out = Path(args.video)
        out.parent.mkdir(parents=True, exist_ok=True)
        with imageio.get_writer(out, fps=args.fps, macro_block_size=1) as w:
            for i, q in enumerate(qpos):
                data.qpos[:] = q
                mujoco.mj_forward(model, data)
                # kamera robotu takip etsin
                cam.lookat[:2] = data.qpos[:2]
                renderer.update_scene(data, camera=cam)
                w.append_data(renderer.render())
                if i % 30 == 0:
                    print(f"  {i}/{len(qpos)}", end="\r")
        print(f"\nvideo -> {out}")
    else:
        from mujoco import viewer as mj_viewer

        print("Pencere aciliyor — kapatmak icin ESC")
        with mj_viewer.launch_passive(model, data) as v:
            import time
            while v.is_running():
                for q in qpos:
                    if not v.is_running():
                        break
                    data.qpos[:] = q
                    mujoco.mj_forward(model, data)
                    v.sync()
                    time.sleep(1 / args.fps)


if __name__ == "__main__":
    main()
