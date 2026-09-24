"""CMU BVH dosyalarini analiz eder ve G1 icin uygunlugunu puanlar.

AMASS/retarget beklemeden hangi hareketlerin ise yarayacagini secmek icin.
BVH'yi dogrudan okur, hareket metriklerini cikarir:

  - sure, kare sayisi
  - kalca yuksekligi (comelme / siçrama tespiti)
  - havada faz (iki ayak da yerden kesik mi) -> ucan teknik
  - bacak/kol aci araliklari -> hareketin genligi
  - hiz zirveleri -> vurus var mi

G1 uygunlugu:
  havada faz uzunsa   -> riskli (inis darbesi)
  kalca cok alcaksa   -> yere inme, G1 kalkamaz
  hareket cok azsa    -> bos klip

Kullanim:
    python scripts/analyze_bvh.py
    python scripts/analyze_bvh.py --dir data/combat_bvh --csv rapor.csv
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def read_bvh(path: Path):
    """BVH -> (kanal adlari, hareket matrisi, frame_time). Saf metin ayristirma."""
    txt = path.read_text(errors="replace").splitlines()
    joints, channels = [], []
    cur = None
    i = 0
    for i, line in enumerate(txt):
        s = line.strip()
        if s.startswith(("ROOT", "JOINT")):
            cur = s.split()[1]
            joints.append(cur)
        elif s.startswith("CHANNELS"):
            parts = s.split()
            for c in parts[2:]:
                channels.append(f"{cur}.{c}")
        elif s.startswith("MOTION"):
            break

    frame_time = 1 / 120
    start = None
    for j in range(i, min(i + 6, len(txt))):
        s = txt[j].strip()
        if s.startswith("Frame Time:"):
            frame_time = float(s.split(":")[1])
            start = j + 1
    if start is None:
        raise ValueError("Frame Time yok")

    data = np.array([[float(x) for x in ln.split()] for ln in txt[start:] if ln.strip()])
    return channels, data, frame_time


def analyze(path: Path) -> dict:
    ch, d, ft = read_bvh(path)
    fps = round(1 / ft)
    n = len(d)

    # Kok yukseklik kanali (CMU: Hips.Yposition)
    yi = next((k for k, c in enumerate(ch) if c.endswith("Yposition")), 1)
    hip = d[:, yi]

    # Ayak eklemlerinin acilari degil, kok yuksekligi uzerinden kaba tahmin.
    # CMU birimi inch; ~1 inch = 2.54 cm. Tipik kalca ~36 inch.
    hip_n = hip / (np.median(hip) + 1e-9)     # medyana normalize

    # Rotasyon kanallari = hareket genligi
    rot = [k for k, c in enumerate(ch) if c.endswith(("Xrotation", "Yrotation", "Zrotation"))]
    R = d[:, rot]
    per_frame = np.abs(np.diff(R, axis=0)).mean(axis=1) if n > 1 else np.zeros(1)
    speed = float(per_frame.mean())

    # ORTALAMA YANILTIYOR: 83 sn'lik klipte tekme 3 sn surer, ortalama dusuk cikar.
    # 1 sn'lik kayan pencerenin tepesi gercek vurus yogunlugunu verir.
    w = max(1, int(1 / ft))
    if len(per_frame) >= w:
        roll = np.convolve(per_frame, np.ones(w) / w, mode="valid")
        peak = float(roll.max())
        peak_t = float(roll.argmax() * ft)   # vurusun basladigi saniye
    else:
        peak, peak_t = speed, 0.0

    # Bacak kanallari (CMU isimleri)
    leg = [k for k, c in enumerate(ch)
           if any(t in c for t in ("UpLeg", "Leg", "Foot", "Toe")) and "rotation" in c]
    arm = [k for k, c in enumerate(ch)
           if any(t in c for t in ("Arm", "ForeArm", "Hand", "Shoulder")) and "rotation" in c]

    return {
        "dosya": path.name,
        "kare": n,
        "sure_s": round(n * ft, 1),
        "fps": fps,
        # siçrama gostergesi: kalca medyanin %10 uzerine cikmis mi
        "sicrama": round(float(hip_n.max()), 2),
        # comelme/yere inme gostergesi
        "alcalma": round(float(hip_n.min()), 2),
        "hareket": round(float(speed), 2),
        "tepe": round(peak, 2),          # en yogun 1 sn
        "tepe_s": round(peak_t, 1),      # vurusun oldugu an -> buradan kes
        "bacak_max": round(float(np.ptp(d[:, leg], axis=0).max()) if leg else 0, 0),
        "kol_max": round(float(np.ptp(d[:, arm], axis=0).max()) if arm else 0, 0),
    }


def verdict(r: dict) -> str:
    """G1 icin kaba uygunluk. Tepe degeri kullanir — ortalama uzun kliplerde yaniltir."""
    if r["alcalma"] < 0.55:
        return "YERE_INME"       # G1 kalkamaz
    if r["sicrama"] > 1.18:
        return "HAVADA"          # ucan faz — riskli ama tam istedigimiz
    if r["tepe"] < 0.35:
        return "DURGUN"          # hicbir aninda vurus yok
    return "UYGUN"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="data/combat_bvh")
    ap.add_argument("--csv", help="sonuclari CSV'ye yaz")
    args = ap.parse_args()

    files = sorted(Path(args.dir).glob("*.bvh"))
    if not files:
        raise SystemExit(f"BVH yok: {args.dir}")

    rows = []
    for f in files:
        try:
            r = analyze(f)
            r["durum"] = verdict(r)
            rows.append(r)
        except Exception as e:
            print(f"  HATA {f.name}: {type(e).__name__}")

    df = pd.DataFrame(rows).sort_values(["durum", "hareket"], ascending=[True, False])
    print(df.to_string(index=False))

    print("\n--- ozet ---")
    for k, v in df["durum"].value_counts().items():
        print(f"  {k:<12} {v}")
    print(f"\ntoplam sure: {df.sure_s.sum():.0f} s")

    if args.csv:
        df.to_csv(args.csv, index=False)
        print(f"\n-> {args.csv}")


if __name__ == "__main__":
    main()
