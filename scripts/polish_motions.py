"""G1 hareketlerini egitim oncesi temizler.

Denetim 33 klipte 13 sorun buldu:
  - titrek (jitter>1.5): IK cozucunun kare-kare gurultusu
  - egik   (dik<%90)   : govde dikligi kaybi
  - cokme  (ayak_z<0.45): kalca cok alcak

Uygulanan duzeltmeler:

1. **Jitter filtresi** — Savitzky-Golay. Ortalama filtreden iyi:
   vurus tepelerini korurken yuksek frekansli gurultuyu atar.
   Hareketin genligini (diz acisi, sicrama) bozmaz.

2. **Quaternion yumusatma** — slerp yerine bilesen filtresi + normalize.
   Kok donusundeki sicramalar giderilir.

3. **Zemin hizalama** — en dusuk ayak temasini z=0'a oturtur.
   Robotun havada yuzmesini veya yere gommesini onler.

4. **Eklem limiti kirpma** — G1 XML'inden okunan gercek limitler.
   Limit disi acilar IK'yi egitimde patlatir.

Kullanim:
    python scripts/polish_motions.py                  # combos + smart
    python scripts/polish_motions.py --dry-run        # sadece rapor
    python scripts/polish_motions.py --window 9
"""
import argparse
import pickle
from pathlib import Path

import numpy as np
from scipy.signal import savgol_filter
from scipy.spatial.transform import Rotation as R

MODEL = "assets/unitree_g1/scene_hd.xml"
SOURCES = [Path("C:/ufbots_tools/data/g1_combos"), Path("C:/ufbots_tools/data/g1_smart")]
DST = Path("C:/ufbots_tools/data/g1_polished")


def joint_limits():
    """G1 XML'inden eklem limitlerini okur (radyan)."""
    import mujoco
    m = mujoco.MjModel.from_xml_path(MODEL)
    lo, hi = [], []
    for i in range(m.njnt):
        if m.jnt_limited[i]:
            lo.append(m.jnt_range[i][0]); hi.append(m.jnt_range[i][1])
    return np.array(lo), np.array(hi)


def smooth(a: np.ndarray, win: int, poly: int = 3) -> np.ndarray:
    """Savitzky-Golay: tepeleri korur, gurultuyu atar."""
    if len(a) < win or win < poly + 2:
        return a
    win = win if win % 2 else win + 1          # tek sayi olmali
    return savgol_filter(a, win, poly, axis=0)


def foot_height(qpos: np.ndarray) -> np.ndarray:
    """Her karede en dusuk ayak temas yuksekligi."""
    import mujoco
    m = mujoco.MjModel.from_xml_path(MODEL)
    d = mujoco.MjData(m)
    ids = [mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, n)
           for n in ("left_ankle_roll_link", "right_ankle_roll_link")]
    ids = [i for i in ids if i >= 0]
    if not ids:
        return np.zeros(len(qpos))
    out = []
    for q in qpos:
        d.qpos[:] = q
        mujoco.mj_forward(m, d)
        out.append(min(d.xpos[i][2] for i in ids))
    return np.array(out)


def polish(d: dict, win: int, lo, hi) -> tuple[dict, dict]:
    pos = np.asarray(d["root_pos"], float).copy()
    quat = np.asarray(d["root_rot"], float).copy()
    dof = np.asarray(d["dof_pos"], float).copy()

    before = float(np.abs(np.diff(np.rad2deg(dof), axis=0, n=2)).mean()) if len(dof) > 2 else 0

    # 1) eklem + kok yumusatma
    dof = smooth(dof, win)
    pos = smooth(pos, win)

    # 2) quaternion: bilesen filtresi, sonra normalize
    #    once isaret tutarliligi (q ve -q ayni donusu gosterir)
    for i in range(1, len(quat)):
        if np.dot(quat[i], quat[i - 1]) < 0:
            quat[i] = -quat[i]
    quat = smooth(quat, win)
    quat /= np.linalg.norm(quat, axis=1, keepdims=True)

    # 3) eklem limiti kirpma
    n_clip = 0
    if lo is not None and len(lo) == dof.shape[1]:
        clipped = np.clip(dof, lo, hi)
        n_clip = int((clipped != dof).sum())
        dof = clipped

    after = float(np.abs(np.diff(np.rad2deg(dof), axis=0, n=2)).mean()) if len(dof) > 2 else 0

    # 4) zemin hizalama — en dusuk ayak temasini yere otur
    qpos = np.hstack([pos, quat, dof])
    fh = foot_height(qpos)
    shift = float(np.percentile(fh, 2))        # %2'lik dilim = en alt temas
    pos[:, 2] -= shift

    out = {"fps": d["fps"], "root_pos": pos.astype(np.float32),
           "root_rot": quat.astype(np.float32), "dof_pos": dof.astype(np.float32)}
    return out, {"jitter_once": before, "jitter_sonra": after,
                 "kirpilan": n_clip, "zemin_kaydirma": shift}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", nargs="+", default=[str(p) for p in SOURCES])
    ap.add_argument("--dst", default=str(DST))
    ap.add_argument("--window", type=int, default=7, help="yumusatma penceresi (kare)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    try:
        lo, hi = joint_limits()
        print(f"eklem limitleri okundu: {len(lo)} eklem")
    except Exception as e:
        lo = hi = None
        print(f"limit okunamadi ({type(e).__name__}) — kirpma atlanacak")

    dst = Path(args.dst)
    if not args.dry_run:
        dst.mkdir(parents=True, exist_ok=True)

    files = []
    for s in args.src:
        files += sorted(Path(s).glob("*.pkl"))

    print(f"\n{'klip':<26}{'jitter':>16}{'kirp':>7}{'zemin':>8}")
    print("-" * 60)
    tot_clip = 0
    for f in files:
        d = pickle.load(open(f, "rb"))
        out, st = polish(d, args.window, lo, hi)
        tot_clip += st["kirpilan"]
        print(f"{f.stem:<26}{st['jitter_once']:>7.2f}->{st['jitter_sonra']:<7.2f}"
              f"{st['kirpilan']:>7}{st['zemin_kaydirma']:>8.3f}")
        if not args.dry_run:
            pickle.dump(out, open(dst / f.name, "wb"))

    print(f"\n{len(files)} klip | toplam kirpilan aci: {tot_clip}")
    if not args.dry_run:
        print(f"-> {dst}")


if __name__ == "__main__":
    main()
