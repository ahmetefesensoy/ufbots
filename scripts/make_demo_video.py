"""Submission demo videosu uretir.

Yarisma formu "the move, before and after" istiyor. Bu script iki
kaynaktan yan yana video kurar:

    SOL  = referans (bizim hazirladigimiz hedef hareket)
    SAG  = politika ciktisi (egitim sonrasi robotun yaptigi)

Egitim henuz yoksa `--solo` ile tek panel referans videosu uretir —
veri hattinin calistigini gosterir.

Ustune baslik + metrik yazisi basar (diz acisi, sicrama).

Kullanim:
    python scripts/make_demo_video.py --solo --clip chanleak
    python scripts/make_demo_video.py --left <ref.pkl> --right <policy.pkl>
"""
import argparse
import pickle
from pathlib import Path

import numpy as np

MODEL = "assets/unitree_g1/scene_hd.xml"
CURATED = Path("C:/ufbots_tools/data/g1_curated/train")


def load(p: Path):
    d = pickle.load(open(p, "rb"))
    n = len(d["root_pos"])
    q = np.zeros((n, 36))
    q[:, 0:3] = d["root_pos"]; q[:, 3:7] = d["root_rot"]; q[:, 7:] = d["dof_pos"]
    return q, float(np.asarray(d["fps"]))


def metrics(q: np.ndarray) -> str:
    j = np.rad2deg(q[:, 7:]); z = q[:, 2]
    diz = max(np.ptp(j[:, 3]), np.ptp(j[:, 9]))
    return f"diz {diz:.0f}deg | sicrama {z.max()/np.median(z):.2f}"


def render(qpos, fps, w=960, h=720, label=""):
    import mujoco
    m = mujoco.MjModel.from_xml_path(MODEL)
    d = mujoco.MjData(m)
    r = mujoco.Renderer(m, height=h, width=w)
    cam = mujoco.MjvCamera(); mujoco.mjv_defaultCamera(cam)
    cam.distance, cam.elevation, cam.azimuth = 2.6, -10, 150

    step = max(1, int(fps // 30))
    frames = []
    for fr in qpos[::step]:
        d.qpos[:] = fr
        mujoco.mj_forward(m, d)
        cam.lookat[:2] = d.qpos[:2]; cam.lookat[2] = 0.8
        r.update_scene(d, camera=cam)
        frames.append(r.render())
    return frames


def annotate(img, lines, y0=28):
    """PIL ile ustune yazi basar (font yoksa sessizce atlar)."""
    try:
        from PIL import Image, ImageDraw
        im = Image.fromarray(img); dr = ImageDraw.Draw(im)
        for i, t in enumerate(lines):
            dr.text((16, y0 + i * 22), t, fill=(255, 255, 255))
        return np.asarray(im)
    except Exception:
        return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clip", default="chanleak")
    ap.add_argument("--left"); ap.add_argument("--right")
    ap.add_argument("--solo", action="store_true", help="tek panel (egitim yoksa)")
    ap.add_argument("--out", default="results/demo.mp4")
    args = ap.parse_args()

    import imageio.v2 as imageio

    if args.solo or not args.right:
        src = Path(args.left) if args.left else CURATED / f"{args.clip}.pkl"
        if not src.exists():
            raise SystemExit(f"klip yok: {src}")
        q, fps = load(src)
        fr = render(q, fps, 1280, 720)
        fr = [annotate(f, [f"ufbots — {src.stem}", metrics(q),
                           "referans hareket (egitim oncesi)"]) for f in fr]
        title = "tek panel"
    else:
        ql, fl = load(Path(args.left)); qr, fr_ = load(Path(args.right))
        a = render(ql, fl, 960, 720); b = render(qr, fr_, 960, 720)
        n = min(len(a), len(b))
        a = [annotate(x, ["REFERANS", metrics(ql)]) for x in a[:n]]
        b = [annotate(x, ["POLITIKA", metrics(qr)]) for x in b[:n]]
        fr = [np.hstack([x, y]) for x, y in zip(a, b)]
        title = "yan yana"

    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    with imageio.get_writer(out, fps=30, macro_block_size=1) as w:
        for f in fr:
            w.append_data(f)
    print(f"{title}: {len(fr)} kare ({len(fr)/30:.1f}s) -> {out}")


if __name__ == "__main__":
    main()
