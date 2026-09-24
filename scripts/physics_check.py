"""Hareketleri GERCEK FIZIK altinda test eder.

Simdiye kadar yaptigimiz her sey kinematikti: eklem acilarini dogrudan
qpos'a yaziyorduk, yercekimi/temas/tork yoktu. Robot havada durabiliyordu.

Bu script MuJoCo fizigini acip PD kontrolcuyle hareketi takip ettiriyor:
  - yercekimi acik
  - ayak-zemin temasi acik
  - eklem torklari sinirli (G1 gercek limitleri)

Olctugu:
  dusme       : govde 0.3 m altina indi mi
  takip_hata  : hedef vs gercek eklem acisi (derece)
  ayak_kayma  : temas halindeki ayagin yatay hareketi
  tork_doyum  : kac kare tork limitine dayandi

Bu, SONIC egitimi oncesi hangi kliplerin fiziksel olarak makul
oldugunu gosterir. Egitim yapmadan "bu hareket G1'de tutar mi"
sorusuna yaklasik cevap verir.

NOT: Bu tam bir egitim degil — PD takibi, ogrenilmis politika degil.
Gercek sonuc SONIC fine-tune sonrasi belli olur.

Kullanim:
    python scripts/physics_check.py
    python scripts/physics_check.py --clip chanleak --video out.mp4
"""
import argparse
import pickle
from pathlib import Path

import numpy as np

MODEL = "assets/unitree_g1/scene_hd.xml"
SRC = Path("C:/ufbots_tools/data/g1_curated/train")

KP = 120.0     # PD orantisal kazanc
KD = 6.0       # turev kazanc
FALL_Z = 0.35  # bu yuksekligin altina inerse dusmus sayilir


def load(p: Path):
    d = pickle.load(open(p, "rb"))
    return (np.asarray(d["root_pos"]), np.asarray(d["root_rot"]),
            np.asarray(d["dof_pos"]), float(np.asarray(d["fps"])))


def simulate(pos, quat, dof, fps, record=False):
    import mujoco
    m = mujoco.MjModel.from_xml_path(MODEL)
    d = mujoco.MjData(m)

    # baslangic durumu: ilk kare
    d.qpos[0:3] = pos[0]; d.qpos[3:7] = quat[0]; d.qpos[7:] = dof[0]
    mujoco.mj_forward(m, d)

    sub = max(1, int(round(1.0 / fps / m.opt.timestep)))   # kare basina fizik adimi
    nu = m.nu
    lo = m.actuator_ctrlrange[:, 0] if m.actuator_ctrlrange.size else None
    hi = m.actuator_ctrlrange[:, 1] if m.actuator_ctrlrange.size else None

    err, slip, sat, frames = [], [], 0, []
    fell_at = None
    renderer = None
    if record:
        renderer = mujoco.Renderer(m, height=720, width=1280)
        cam = mujoco.MjvCamera(); mujoco.mjv_defaultCamera(cam)
        cam.distance, cam.elevation, cam.azimuth = 2.8, -10, 150

    prev_foot = None
    for i, target in enumerate(dof):
        # G1 XML'inde aktuatorler POZISYON kontrollu (gainprm=500,
        # ctrlrange radyan). Tork degil, hedef ACI yazilir.
        cmd = target[:nu]
        if lo is not None:
            clipped = np.clip(cmd, lo, hi)
            sat += int((clipped != cmd).sum())
            cmd = clipped
        for _ in range(sub):
            d.ctrl[:] = cmd
            mujoco.mj_step(m, d)

        err.append(np.abs(np.rad2deg(d.qpos[7:7 + nu] - target[:nu])).mean())
        if d.qpos[2] < FALL_Z and fell_at is None:
            fell_at = i / fps

        # ayak kaymasi: temas eden ayagin yatay hizi
        foot = []
        for name in ("left_ankle_roll_link", "right_ankle_roll_link"):
            bid = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, name)
            if bid >= 0:
                foot.append(d.xpos[bid].copy())
        if foot and prev_foot:
            for a, b in zip(foot, prev_foot):
                if a[2] < 0.08:                       # yere yakin = temas
                    slip.append(float(np.linalg.norm(a[:2] - b[:2])))
        prev_foot = foot

        if record and i % max(1, int(fps // 30)) == 0:
            cam.lookat[:2] = d.qpos[:2]; cam.lookat[2] = 0.8
            renderer.update_scene(d, camera=cam)
            frames.append(renderer.render())

    return {
        "dusme_s": fell_at,
        "takip_hata": float(np.mean(err)) if err else 0.0,
        "ayak_kayma_mm": float(np.mean(slip) * 1000) if slip else 0.0,
        "tork_doyum": sat,
        "son_z": float(d.qpos[2]),
    }, frames


def verdict(r: dict) -> str:
    if r["dusme_s"] is not None:
        return f"DUSTU {r['dusme_s']:.1f}s"
    if r["takip_hata"] > 25:
        return "takip zayif"
    if r["ayak_kayma_mm"] > 15:
        return "ayak kayiyor"
    return "AYAKTA"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(SRC))
    ap.add_argument("--clip", help="tek klip")
    ap.add_argument("--video", help="mp4 kaydet (tek klip icin)")
    args = ap.parse_args()

    src = Path(args.src)
    files = [src / f"{args.clip}.pkl"] if args.clip else sorted(src.glob("*.pkl"))
    files = [f for f in files if f.exists()]
    if not files:
        raise SystemExit(f"PKL yok: {src}")

    print(f"{'klip':<26}{'takip°':>8}{'kayma_mm':>10}{'doyum':>8}  sonuc")
    print("-" * 66)
    rows = []
    for f in files:
        pos, quat, dof, fps = load(f)
        r, frames = simulate(pos, quat, dof, fps, record=bool(args.video))
        v = verdict(r)
        rows.append((f.stem, r, v))
        print(f"{f.stem:<26}{r['takip_hata']:>8.1f}{r['ayak_kayma_mm']:>10.1f}"
              f"{r['tork_doyum']:>8}  {v}")

        if args.video and frames:
            import imageio.v2 as imageio
            out = Path(args.video); out.parent.mkdir(parents=True, exist_ok=True)
            with imageio.get_writer(out, fps=30, macro_block_size=1) as w:
                for fr in frames:
                    w.append_data(fr)
            print(f"\nvideo -> {out}")

    ok = sum(1 for _, _, v in rows if v == "AYAKTA")
    print(f"\nayakta kalan: {ok}/{len(rows)}")
    print("\nNOT: bu PD takibi, ogrenilmis politika degil. Gercek sonuc")
    print("     SONIC fine-tune sonrasi belli olur — burada dusenler")
    print("     egitimde de zorlanacak demektir.")


if __name__ == "__main__":
    main()
