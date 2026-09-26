"""Submission videosu v2 — dolu kurgu.

v1'de tek klipten 9 saniye vardi; elde 5 dakikalik egitim goruntusu
dururken az kaliyordu. Bu surum:

  1. baslik
  2. problem karti
  3. BEFORE: PD kontrolun 4 klipte ust uste dusmesi (2x2 izgara)
  4. gecis karti
  5. AFTER: egitilmis politikadan 4 farkli kamera/robot (2x2 izgara)
  6. yan yana karsilastirma (ayni anda)
  7. one cikan hareketler (tek tek, buyuk)
  8. metrikler
  9. kredi

Kullanim:
    python scripts/make_submission_video2.py
"""
import argparse
from pathlib import Path

import imageio.v2 as iio
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1920, 1080, 30
BG = (12, 14, 18)
WHITE = (255, 255, 255); GREY = (150, 156, 166)
RED = (235, 90, 80); GREEN = (90, 210, 130)


def font(px, bold=False):
    for n in (["arialbd.ttf", "seguisb.ttf"] if bold else ["arial.ttf", "segoeui.ttf"]):
        try:
            return ImageFont.truetype(n, px)
        except OSError:
            continue
    return ImageFont.load_default()


def centre(d, y, text, f, fill=WHITE):
    w = d.textbbox((0, 0), text, font=f)[2]
    d.text(((W - w) // 2, y), text, font=f, fill=fill)


def card(lines, secs):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    for text, px, bold, col, yr in lines:
        centre(d, int(H * yr), text, font(px, bold), col)
    return [np.asarray(img)] * int(secs * FPS)


def fill(frame, size):
    """Paneli tam doldur: en-boy koru, tas, ortadan kirp."""
    im = Image.fromarray(frame).convert("RGB")
    sc = max(size[0] / im.width, size[1] / im.height)
    im = im.resize((max(1, round(im.width * sc)), max(1, round(im.height * sc))),
                   Image.LANCZOS)
    x, y = (im.width - size[0]) // 2, (im.height - size[1]) // 2
    return im.crop((x, y, x + size[0], y + size[1]))


def load(path, n=None):
    fr = [f for f in iio.get_reader(path)]
    return fr[:n] if n else fr


def grid(clips, secs, title, tcol, offsets=None, labels=None):
    """2x2 izgara. clips: 4 kare listesi."""
    n = int(secs * FPS)
    gw, gh = W // 2, int(H * 0.40)
    top = int(H * 0.13)
    f_t, f_l = font(46, True), font(24)
    offs = offsets or [0] * len(clips)
    out = []
    for i in range(n):
        c = Image.new("RGB", (W, H), BG)
        for k, src in enumerate(clips[:4]):
            j = (offs[k] + i) % len(src) if len(src) < n else min(offs[k] + i, len(src) - 1)
            x, y = (k % 2) * gw, top + (k // 2) * gh
            c.paste(fill(src[j], (gw - 6, gh - 6)), (x + 3, y + 3))
            if labels and k < len(labels):
                d = ImageDraw.Draw(c)
                d.text((x + 16, y + gh - 34), labels[k], font=f_l, fill=(210, 214, 222))
        d = ImageDraw.Draw(c)
        centre(d, int(H * 0.035), title, f_t, tcol)
        out.append(np.asarray(c))
    return out


def side_by_side(left, right, lo, ro, secs):
    n = int(secs * FPS)
    pane = (W // 2, int(H * 0.78))
    f_lab, f_sub = font(40, True), font(26)
    out = []
    for i in range(n):
        c = Image.new("RGB", (W, H), BG)
        for src, off, x0, (lab, sub, col) in (
            (left, lo, 0, ("BEFORE — PD control", "joint error 3.3 deg", RED)),
            (right, ro, W // 2, ("AFTER — trained policy", "61% success rate", GREEN)),
        ):
            j = (off + i) % len(src) if len(src) < n else min(off + i, len(src) - 1)
            c.paste(fill(src[j], pane), (x0, int(H * 0.10)))
            d = ImageDraw.Draw(c)
            w = d.textbbox((0, 0), lab, font=f_lab)[2]
            d.text((x0 + (W // 2 - w) // 2, int(H * 0.025)), lab, font=f_lab, fill=col)
            w = d.textbbox((0, 0), sub, font=f_sub)[2]
            d.text((x0 + (W // 2 - w) // 2, int(H * 0.925)), sub, font=f_sub, fill=GREY)
        d = ImageDraw.Draw(c)
        d.line([(W // 2, int(H * 0.08)), (W // 2, int(H * 0.90))],
               fill=(45, 50, 58), width=3)
        out.append(np.asarray(c))
    return out


def feature(src, off, secs, caption):
    """Tek klip, tam ekran, altta aciklama."""
    n = int(secs * FPS)
    f = font(34, True)
    out = []
    for i in range(n):
        j = min(off + i, len(src) - 1)
        c = Image.new("RGB", (W, H), BG)
        c.paste(fill(src[j], (W, int(H * 0.86))), (0, 0))
        d = ImageDraw.Draw(c)
        centre(d, int(H * 0.90), caption, f, WHITE)
        out.append(np.asarray(c))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--out", default="results/submission_video.mp4")
    a = ap.parse_args()

    T = Path("results/trained")
    print("egitim klipleri yukleniyor...")
    A = {i: load(T / f"00000{i}.mp4") for i in (0, 2, 3, 4, 5, 6)}

    print("PD klipleri yukleniyor...")
    want = ["chanleak", "jump_kick_86_01", "knee_strike_86_06",
            "punch_kick_combo_86_08"]
    pd_files = [Path(f"results/before_{w}_pd.mp4") for w in want]
    pd_files = [p for p in pd_files if p.exists()] or                sorted(Path("results").glob("before_*_pd.mp4"))
    P = [load(p) for p in pd_files]
    pd_names = [p.stem.replace("before_", "").replace("_pd", "") for p in pd_files]
    print("  PD:", ", ".join(pd_names))

    seq = []
    seq += card([
        ("CHANLEAK", 110, True, WHITE, 0.30),
        ("Bokator on a Unitree G1", 44, False, GREY, 0.45),
        ("fine-tuned from NVIDIA SONIC", 28, False, GREY, 0.54),
    ], 3.0)

    seq += card([
        ("The motions were correct.", 54, True, WHITE, 0.34),
        ("Retargeted clips tracked joint angles", 32, False, GREY, 0.47),
        ("to within 3 degrees under full physics.", 32, False, GREY, 0.54),
    ], 3.5)

    # BEFORE izgara
    if len(P) >= 4:
        seq += grid(P[:4], 6.0, "BEFORE — PD control", RED,
                    labels=[n.replace("_", " ") for n in pd_names[:4]])
    seq += card([
        ("All 32 fell within 1.1 seconds.", 54, True, RED, 0.42),
        ("Kinematic correctness is not balance.", 32, False, GREY, 0.54),
    ], 3.5)

    # AFTER izgara
    seq += grid([A[0], A[2], A[4], A[6]], 8.0, "AFTER — trained policy", GREEN,
                offsets=[120, 200, 90, 260])

    # yan yana
    seq += card([("Same motion, side by side.", 46, True, WHITE, 0.44)], 2.0)
    seq += side_by_side(P[0], A[4], 0, 90, 8.0)

    # one cikanlar
    seq += card([("Techniques", 52, True, WHITE, 0.44)], 2.0)
    # kare numaralari find_moments.py ile olculdu, tahmin degil
    seq += feature(A[5], 300, 4.5, "airborne knee  ·  peak hip height")
    seq += feature(A[4], 800, 4.5, "extended strike  ·  widest reach")
    seq += feature(A[2], 865, 4.5, "lunge punch  ·  recovers to guard")
    seq += feature(A[6], 770, 4.5, "spinning technique  ·  balance held")
    seq += feature(A[3], 940, 4.5, "high kick  ·  one-leg support")

    seq += card([
        ("RESULTS", 44, True, GREY, 0.20),
        ("PD control            0% success", 42, False, RED, 0.34),
        ("Trained policy       61% success", 42, True, GREEN, 0.43),
        ("mpjpe_g   189 mm   (target <200)", 32, False, GREY, 0.56),
        ("6,933 iterations  ·  single NVIDIA L4  ·  ~10 GPU-hours", 26, False, GREY, 0.64),
    ], 5.0)

    seq += card([
        ("Motion Data by Bones Studio", 46, True, WHITE, 0.42),
        ("CMU Mocap · AMASS · GMR · BONES-SEED · GR00T-WBC", 24, False, GREY, 0.53),
    ], 3.5)

    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    with iio.get_writer(out, fps=FPS, quality=8, macro_block_size=1) as w:
        for f in seq:
            w.append_data(f)
    print(f"\n{len(seq)} kare ({len(seq)/FPS:.1f}s) -> {out}")


if __name__ == "__main__":
    main()
