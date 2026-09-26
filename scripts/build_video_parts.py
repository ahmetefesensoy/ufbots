"""Videoyu PARCA PARCA uretir, sonra birlestirir.

Tek seferde uretmek bu makinede tikaniyor: C: dolu oldugu icin Windows
sayfa dosyasini buyutemiyor ve ffmpeg 10 MB'lik ayirmalari bile
yapamiyor ("Cannot allocate memory"). Her parca ayri bir ffmpeg
surecinde uretilip kapatilinca bellek geri veriliyor.

Cozunurluk 1080p yerine 720p: bellek ihtiyaci ~2.2 kat dusuyor,
YouTube icin fazlasiyla yeterli.

Kullanim:
    python scripts/build_video_parts.py --outdir /d/ufbots_video
"""
import argparse
import gc
from pathlib import Path

import imageio.v2 as iio
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1280, 720, 30
BG = (12, 14, 18)
WHITE = (255, 255, 255)
GREY = (150, 156, 166)
RED = (235, 90, 80)
GREEN = (90, 210, 130)
T = Path("results/trained")


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


def fill_pane(frame, size):
    """Paneli tam doldur: en-boy koru, tas, ortadan kirp."""
    im = Image.fromarray(frame).convert("RGB")
    sc = max(size[0] / im.width, size[1] / im.height)
    im = im.resize((max(1, round(im.width * sc)), max(1, round(im.height * sc))),
                   Image.LANCZOS)
    x, y = (im.width - size[0]) // 2, (im.height - size[1]) // 2
    return im.crop((x, y, x + size[0], y + size[1]))


def read_window(path, start, count, shrink=2):
    """Bir dosyadan sadece istenen araligi oku, okurken kucult."""
    fr = []
    rd = iio.get_reader(path)
    try:
        for i, f in enumerate(rd):
            if i < start:
                continue
            fr.append(f[::shrink, ::shrink])
            if len(fr) >= count:
                break
    except Exception as e:
        print(f"    uyari: {Path(path).name} kare {start + len(fr)} ({type(e).__name__})")
    finally:
        rd.close()
    return fr


def write(path, frames_iter):
    with iio.get_writer(path, fps=FPS, quality=7, macro_block_size=1) as w:
        n = 0
        for f in frames_iter:
            w.append_data(f)
            n += 1
    gc.collect()
    print(f"  -> {Path(path).name}  {n} kare ({n / FPS:.1f}s)")
    return n


def gen_card(lines, secs):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    for text, px, bold, col, yr in lines:
        centre(d, int(H * yr), text, font(px, bold), col)
    a = np.asarray(img)
    for _ in range(int(secs * FPS)):
        yield a


def gen_grid(clips, secs, title, tcol, labels=None):
    n = int(secs * FPS)
    gw, gh = W // 2, int(H * 0.40)
    top = int(H * 0.13)
    f_t, f_l = font(31, True), font(16)
    for i in range(n):
        c = Image.new("RGB", (W, H), BG)
        for k, src in enumerate(clips[:4]):
            if not src:
                continue
            j = i % len(src) if len(src) < n else min(i, len(src) - 1)
            x, y = (k % 2) * gw, top + (k // 2) * gh
            c.paste(fill_pane(src[j], (gw - 4, gh - 4)), (x + 2, y + 2))
            if labels and k < len(labels):
                ImageDraw.Draw(c).text((x + 12, y + gh - 24), labels[k],
                                       font=f_l, fill=(210, 214, 222))
        centre(ImageDraw.Draw(c), int(H * 0.035), title, f_t, tcol)
        yield np.asarray(c)


def gen_sbs(left, right, secs):
    n = int(secs * FPS)
    pane = (W // 2, int(H * 0.78))
    f_lab, f_sub = font(27, True), font(17)
    spec = ((left, 0, ("BEFORE - PD control", "joint error 3.3 deg", RED)),
            (right, W // 2, ("AFTER - trained policy", "61% success rate", GREEN)))
    for i in range(n):
        c = Image.new("RGB", (W, H), BG)
        for src, x0, (lab, sub, col) in spec:
            if not src:
                continue
            j = i % len(src) if len(src) < n else min(i, len(src) - 1)
            c.paste(fill_pane(src[j], pane), (x0, int(H * 0.10)))
            d = ImageDraw.Draw(c)
            w = d.textbbox((0, 0), lab, font=f_lab)[2]
            d.text((x0 + (W // 2 - w) // 2, int(H * 0.025)), lab, font=f_lab, fill=col)
            w = d.textbbox((0, 0), sub, font=f_sub)[2]
            d.text((x0 + (W // 2 - w) // 2, int(H * 0.925)), sub, font=f_sub, fill=GREY)
        ImageDraw.Draw(c).line([(W // 2, int(H * 0.08)), (W // 2, int(H * 0.90))],
                               fill=(45, 50, 58), width=2)
        yield np.asarray(c)


def gen_feature(src, secs, caption):
    n = int(secs * FPS)
    f = font(23, True)
    for i in range(n):
        j = min(i, len(src) - 1)
        c = Image.new("RGB", (W, H), BG)
        c.paste(fill_pane(src[j], (W, int(H * 0.86))), (0, 0))
        centre(ImageDraw.Draw(c), int(H * 0.90), caption, f, WHITE)
        yield np.asarray(c)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default="/d/ufbots_video")
    a = ap.parse_args()
    od = Path(a.outdir)
    od.mkdir(parents=True, exist_ok=True)
    parts = []

    def part(name):
        p = od / f"p{len(parts):02d}_{name}.mp4"
        parts.append(p)
        return p

    print("[1/6] kartlar")
    write(part("intro"), gen_card([
        ("CHANLEAK", 74, True, WHITE, 0.30),
        ("Bokator on a Unitree G1", 30, False, GREY, 0.45),
        ("fine-tuned from NVIDIA SONIC", 19, False, GREY, 0.54)], 3.0))
    write(part("problem"), gen_card([
        ("The motions were correct.", 36, True, WHITE, 0.34),
        ("Retargeted clips tracked joint angles", 21, False, GREY, 0.47),
        ("to within 3 degrees under full physics.", 21, False, GREY, 0.54)], 3.5))

    print("[2/6] BEFORE izgara")
    want = ["chanleak", "jump_kick_86_01", "knee_strike_86_06",
            "punch_kick_combo_86_08"]
    pdf = [Path(f"results/before_{w}_pd.mp4") for w in want]
    pdf = [q for q in pdf if q.exists()]
    P = [read_window(q, 0, 180, shrink=2) for q in pdf]
    labels = [q.stem.replace("before_", "").replace("_pd", "").replace("_", " ")
              for q in pdf]
    write(part("before"), gen_grid(P, 6.0, "BEFORE - PD control", RED, labels=labels))
    sbs_left = P[0] if P else []
    P = None
    gc.collect()

    write(part("finding"), gen_card([
        ("All 32 fell within 1.1 seconds.", 36, True, RED, 0.42),
        ("Kinematic correctness is not balance.", 21, False, GREY, 0.54)], 3.5))

    print("[3/6] AFTER izgara")
    G = [read_window(T / f"00000{v}.mp4", o, 240, shrink=3)
         for v, o in ((0, 120), (2, 200), (4, 90), (6, 260))]
    write(part("after"), gen_grid(G, 8.0, "AFTER - trained policy", GREEN))
    G = None
    gc.collect()

    print("[4/6] yan yana")
    write(part("sbslabel"), gen_card(
        [("Same motion, side by side.", 31, True, WHITE, 0.44)], 2.0))
    R = read_window(T / "000004.mp4", 90, 240, shrink=2)
    write(part("sbs"), gen_sbs(sbs_left, R, 8.0))
    R = sbs_left = None
    gc.collect()

    print("[5/6] teknikler")
    write(part("techlabel"), gen_card(
        [("Techniques", 35, True, WHITE, 0.44)], 2.0))
    for v, off, cap in (
        (5, 300, "airborne knee  -  peak hip height"),
        (4, 800, "extended strike  -  widest reach"),
        (2, 865, "lunge punch  -  recovers to guard"),
        (6, 770, "spinning technique  -  balance held"),
        (3, 940, "high kick  -  one-leg support"),
    ):
        fr = read_window(T / f"00000{v}.mp4", off, 137, shrink=2)
        if fr:
            write(part(f"tech{v}"), gen_feature(fr, 4.5, cap))
        fr = None
        gc.collect()

    print("[6/6] kapanis")
    write(part("results"), gen_card([
        ("RESULTS", 30, True, GREY, 0.20),
        ("PD control            0% success", 29, False, RED, 0.34),
        ("Trained policy       61% success", 29, True, GREEN, 0.43),
        ("mpjpe_g   189 mm   (target <200)", 22, False, GREY, 0.56),
        ("6,933 iterations - single NVIDIA L4", 18, False, GREY, 0.64)], 5.0))
    write(part("credit"), gen_card([
        ("Motion Data by Bones Studio", 31, True, WHITE, 0.42),
        ("CMU Mocap - AMASS - GMR - BONES-SEED - GR00T-WBC", 16, False, GREY, 0.53)], 3.5))

    ok = [p for p in parts if p.exists()]
    lst = od / "parts.txt"
    lst.write_text("".join(f"file '{p.name}'\n" for p in ok), encoding="utf-8")
    print(f"\n{len(ok)} parca -> {od}")


if __name__ == "__main__":
    main()
