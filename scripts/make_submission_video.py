"""Submission videosu: PD kontrol vs egitilmis politika, yan yana.

Iki kaynak farkli sahnede render edildi (PD mavi zemin, politika gri),
bu yuzden kesme yerine BOLUNMUS EKRAN kullaniyoruz — yargicin ayni anda
ikisini gormesi zaten daha guclu.

Yapi:
    1. baslik karti
    2. bolunmus ekran: solda PD (duser), sagda politika (ayakta)
    3. kapanis: metrikler + Bones Studio kredisi

Kullanim:
    python scripts/make_submission_video.py
"""
import argparse
from pathlib import Path

import imageio.v2 as iio
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1920, 1080, 30
PANE = (W // 2, int(H * 0.78))          # her panel

BEFORE = "results/before_chanleak_pd.mp4"
AFTER = "results/trained/000004.mp4"


def font(px, bold=False):
    names = (["arialbd.ttf", "seguisb.ttf"] if bold else ["arial.ttf", "segoeui.ttf"])
    for n in names:
        try:
            return ImageFont.truetype(n, px)
        except OSError:
            continue
    return ImageFont.load_default()


def centre(d, y, text, f, fill=(255, 255, 255)):
    w = d.textbbox((0, 0), text, font=f)[2]
    d.text(((W - w) // 2, y), text, font=f, fill=fill)


def card(lines, secs, bg=(12, 14, 18)):
    """lines: (metin, px, kalin, renk, y_oran)"""
    img = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(img)
    for text, px, bold, col, yr in lines:
        centre(d, int(H * yr), text, font(px, bold), col)
    return [np.asarray(img)] * int(secs * FPS)


def read_frames(path, n=None):
    fr = [f for f in iio.get_reader(path)]
    return fr[:n] if n else fr


def fit(frame, size):
    """Paneli TAM doldur: en-boy koru, tas, ortadan kirp.

    Iki kaynak farkli cozunurlukte (720p vs 1088p); thumbnail kullanilirsa
    biri kucuk kalir ve yan yana dengesiz gorunur.
    """
    im = Image.fromarray(frame).convert("RGB")
    sc = max(size[0] / im.width, size[1] / im.height)
    im = im.resize((max(1, round(im.width * sc)), max(1, round(im.height * sc))),
                   Image.LANCZOS)
    x, y = (im.width - size[0]) // 2, (im.height - size[1]) // 2
    return im.crop((x, y, x + size[0], y + size[1]))


def split_screen(left, right, lo, ro, secs):
    """Iki videoyu yan yana, altyazili. lo/ro = baslangic karesi."""
    n = int(secs * FPS)
    f_lab, f_sub = font(40, True), font(26)
    out = []
    for i in range(n):
        canvas = Image.new("RGB", (W, H), (12, 14, 18))
        for src, off, x0, (lab, sub, col) in (
            (left, lo, 0, ("BEFORE — PD control", "joint error 3.3 deg", (235, 90, 80))),
            (right, ro, W // 2, ("AFTER — trained policy", "61% success rate", (90, 210, 130))),
        ):
            j = (off + i) % len(src) if len(src) < n else min(off + i, len(src) - 1)
            canvas.paste(fit(src[j], PANE), (x0, int(H * 0.10)))
            d = ImageDraw.Draw(canvas)
            w = d.textbbox((0, 0), lab, font=f_lab)[2]
            d.text((x0 + (W // 2 - w) // 2, int(H * 0.025)), lab, font=f_lab, fill=col)
            w = d.textbbox((0, 0), sub, font=f_sub)[2]
            d.text((x0 + (W // 2 - w) // 2, int(H * 0.925)), sub,
                   font=f_sub, fill=(165, 170, 180))
        d = ImageDraw.Draw(canvas)
        d.line([(W // 2, int(H * 0.08)), (W // 2, int(H * 0.90))],
               fill=(45, 50, 58), width=3)
        out.append(np.asarray(canvas))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--before", default=BEFORE)
    ap.add_argument("--after", default=AFTER)
    ap.add_argument("--after-start", type=int, default=90)
    ap.add_argument("-o", "--out", default="results/submission_video.mp4")
    a = ap.parse_args()

    L, R = read_frames(a.before), read_frames(a.after)
    print(f"before {len(L)} kare · after {len(R)} kare")

    W_ = (255, 255, 255); G = (150, 156, 166); A = (90, 210, 130)
    seq = []
    seq += card([
        ("G1 CHANLEAK", 96, True, W_, 0.33),
        ("Bokator's flying knee on a Unitree G1", 40, False, G, 0.46),
        ("SONIC / GR00T-WholeBodyControl fine-tune", 30, False, G, 0.54),
    ], 3.0)
    seq += card([
        ("Kinematically correct is not balanced.", 52, True, W_, 0.38),
        ("Every clip tracked joint angles to within 3 degrees.", 32, False, G, 0.50),
        ("All 32 fell within 1.1 seconds.", 32, False, (235, 90, 80), 0.57),
    ], 3.5)
    seq += split_screen(L, R, 0, a.after_start, 9.0)
    seq += card([
        ("RESULTS", 44, True, G, 0.24),
        ("PD control            0% success", 40, False, (235, 90, 80), 0.38),
        ("Trained policy       61% success", 40, True, A, 0.46),
        ("mpjpe_g  189 mm   (target <200)", 32, False, G, 0.58),
        ("6,933 iterations · single NVIDIA L4", 28, False, G, 0.66),
    ], 4.5)
    seq += card([
        ("Motion Data by Bones Studio", 44, True, W_, 0.44),
        ("CMU Mocap · AMASS · GMR · BONES-SEED", 26, False, G, 0.54),
    ], 3.0)

    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    with iio.get_writer(out, fps=FPS, quality=8, macro_block_size=1) as w:
        for f in seq:
            w.append_data(f)
    print(f"{len(seq)} kare ({len(seq)/FPS:.1f}s) -> {out}")


if __name__ == "__main__":
    main()
