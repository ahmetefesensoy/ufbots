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
    a = np.asarray(img)
    for _ in range(int(secs * FPS)):
        yield a


def fill(frame, size):
    """Paneli tam doldur: en-boy koru, tas, ortadan kirp."""
    im = Image.fromarray(frame).convert("RGB")
    sc = max(size[0] / im.width, size[1] / im.height)
    im = im.resize((max(1, round(im.width * sc)), max(1, round(im.height * sc))),
                   Image.LANCZOS)
    x, y = (im.width - size[0]) // 2, (im.height - size[1]) // 2
    return im.crop((x, y, x + size[0], y + size[1]))


def load(path, start=0, count=None, shrink=2):
    """Sadece gereken araligi oku, okurken kucult.

    Tum klibi RAM'e almak 1080p'de klip basina ~3.5 GB ediyordu; 6 klip
    birden acilinca hem yavasliyor hem kiriliyordu. Burada yalnizca
    kullanacagimiz pencereyi aliyoruz.
    """
    fr = []
    rd = iio.get_reader(path)
    try:
        for i, f in enumerate(rd):
            if i < start:
                continue
            fr.append(f[::shrink, ::shrink] if shrink > 1 else f)
            if count and len(fr) >= count:
                break
    except Exception as e:
        print(f"  uyari: {Path(path).name} kare {start+len(fr)} ({type(e).__name__}: {e})")
    finally:
        rd.close()          # Windows'ta acik reader birikince ffmpeg borulari tukeniyor
    if not fr:
        raise SystemExit(f"okunamadi: {path}")
    return fr


def load_windows(path, wins, shrink=3):
    """Bir dosyayi BIR KEZ acip istenen tum pencereleri toplar.

    Ayni dosyayi birden fazla kez acmak Windows'ta ffmpeg borularini
    tuketiyor ve ikinci acilis sessizce bos donuyordu.

    wins: [(start, count), ...]  ->  [[kare...], ...]
    """
    out = [[] for _ in wins]
    last = max(s0 + c for s0, c in wins)
    rd = iio.get_reader(path)
    try:
        for i, f in enumerate(rd):
            if i >= last:
                break
            sm = None
            for k, (s0, c) in enumerate(wins):
                if s0 <= i < s0 + c:
                    if sm is None:
                        sm = f[::shrink, ::shrink] if shrink > 1 else f
                    out[k].append(sm)
    except Exception as e:
        print(f"  uyari: {Path(path).name} kare {i} ({type(e).__name__})")
    finally:
        rd.close()
    return out


def grid(clips, secs, title, tcol, offsets=None, labels=None):
    """2x2 izgara. clips: 4 kare listesi."""
    n = int(secs * FPS)
    gw, gh = W // 2, int(H * 0.40)
    top = int(H * 0.13)
    f_t, f_l = font(46, True), font(24)
    offs = offsets or [0] * len(clips)
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
        yield np.asarray(c)


def side_by_side(left, right, lo, ro, secs):
    n = int(secs * FPS)
    pane = (W // 2, int(H * 0.78))
    f_lab, f_sub = font(40, True), font(26)
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
        yield np.asarray(c)


def feature(src, off, secs, caption):
    """Tek klip, tam ekran, altta aciklama."""
    n = int(secs * FPS)
    if off + n > len(src):                      # istenen an klibin disinda
        off = max(0, len(src) - n)              # sona sigdir
    f = font(34, True)
    for i in range(n):
        j = min(off + i, len(src) - 1)
        c = Image.new("RGB", (W, H), BG)
        c.paste(fill(src[j], (W, int(H * 0.86))), (0, 0))
        d = ImageDraw.Draw(c)
        centre(d, int(H * 0.90), caption, f, WHITE)
        yield np.asarray(c)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--out", default="results/submission_video.mp4")
    a = ap.parse_args()

    T = Path("results/trained")

    GRID_N, SBS_N, FEAT_N = int(8.0 * FPS), int(8.0 * FPS), int(4.5 * FPS) + 2

    # Her dosyadan hangi pencereler lazim -> tek geciste topla
    need = {
        0: [("grid", 0, GRID_N)],
        2: [("grid", 200, GRID_N), ("feat", 865, FEAT_N)],
        3: [("feat", 940, FEAT_N)],
        4: [("grid", 90, GRID_N), ("feat", 800, FEAT_N), ("sbs", 90, SBS_N)],
        5: [("feat", 300, FEAT_N)],
        6: [("grid", 260, GRID_N), ("feat", 770, FEAT_N)],
    }
    got = {}
    for vid, wins in need.items():
        print(f"  00000{vid}.mp4 ({len(wins)} pencere)...")
        res = load_windows(T / f"00000{vid}.mp4", [(s0, c) for _, s0, c in wins])
        for (tag, s0, _), frames in zip(wins, res):
            got[(vid, tag)] = frames

    G = [got[(0, "grid")], got[(2, "grid")], got[(4, "grid")], got[(6, "grid")]]
    sbs_after = got[(4, "sbs")]
    F = [
        (got[(5, "feat")], "airborne knee  ·  peak hip height"),
        (got[(4, "feat")], "extended strike  ·  widest reach"),
        (got[(2, "feat")], "lunge punch  ·  recovers to guard"),
        (got[(6, "feat")], "spinning technique  ·  balance held"),
        (got[(3, "feat")], "high kick  ·  one-leg support"),
    ]

    print("PD klipleri...")
    want = ["chanleak", "jump_kick_86_01", "knee_strike_86_06",
            "punch_kick_combo_86_08"]
    pd_files = [Path(f"results/before_{w}_pd.mp4") for w in want]
    pd_files = [q for q in pd_files if q.exists()] or                sorted(Path("results").glob("before_*_pd.mp4"))
    P = [load(q) for q in pd_files[:4]]
    pd_names = [q.stem.replace("before_", "").replace("_pd", "") for q in pd_files[:4]]
    print("  PD:", ", ".join(pd_names))

    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)

    # Bolumleri TEMBEL tanimla: kareler ancak yaziciya giderken uretilir.
    # Hepsini listede tutmak 2100 kare x 1920x1080x3 = ~13 GB ediyordu.
    def sections():
        yield card([
            ("CHANLEAK", 110, True, WHITE, 0.30),
            ("Bokator on a Unitree G1", 44, False, GREY, 0.45),
            ("fine-tuned from NVIDIA SONIC", 28, False, GREY, 0.54),
        ], 3.0)
        yield card([
            ("The motions were correct.", 54, True, WHITE, 0.34),
            ("Retargeted clips tracked joint angles", 32, False, GREY, 0.47),
            ("to within 3 degrees under full physics.", 32, False, GREY, 0.54),
        ], 3.5)
        yield grid(P, 6.0, "BEFORE — PD control", RED,
                   labels=[n.replace("_", " ") for n in pd_names])
        yield card([
            ("All 32 fell within 1.1 seconds.", 54, True, RED, 0.42),
            ("Kinematic correctness is not balance.", 32, False, GREY, 0.54),
        ], 3.5)
        yield grid(G, 8.0, "AFTER — trained policy", GREEN)
        yield card([("Same motion, side by side.", 46, True, WHITE, 0.44)], 2.0)
        yield side_by_side(P[0], sbs_after, 0, 0, 8.0)
        yield card([("Techniques", 52, True, WHITE, 0.44)], 2.0)
        for frames, cap in F:
            yield feature(frames, 0, 4.5, cap)
        yield card([
            ("RESULTS", 44, True, GREY, 0.20),
            ("PD control            0% success", 42, False, RED, 0.34),
            ("Trained policy       61% success", 42, True, GREEN, 0.43),
            ("mpjpe_g   189 mm   (target <200)", 32, False, GREY, 0.56),
            ("6,933 iterations  ·  single NVIDIA L4  ·  ~10 GPU-hours", 26, False, GREY, 0.64),
        ], 5.0)
        yield card([
            ("Motion Data by Bones Studio", 46, True, WHITE, 0.42),
            ("CMU Mocap · AMASS · GMR · BONES-SEED · GR00T-WBC", 24, False, GREY, 0.53),
        ], 3.5)

    n = 0
    print("yaziliyor...")
    with iio.get_writer(out, fps=FPS, quality=8, macro_block_size=1) as w:
        for sec in sections():
            for f in sec:
                w.append_data(f)
                n += 1
                if n % 300 == 0:
                    print(f"  {n} kare ({n/FPS:.0f}s)")
    print(f"BITTI: {n} kare ({n/FPS:.1f}s) -> {out}")


if __name__ == "__main__":
    main()
