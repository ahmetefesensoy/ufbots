"""data/kimodo_csv altindaki tum hareketleri render eder + kontak sayfasi uretir.

8 istemi tek tek elle cevirmemek icin.

Kullanim:
    python scripts/render_all.py                  # her istemin ilk ornegi
    python scripts/render_all.py --all            # tum ornekler
    python scripts/render_all.py --frames 120     # kisa tut (hizli)
"""
import argparse
import subprocess
import sys
from pathlib import Path

SRC = Path("data/kimodo_csv")
OUT = Path("results/kimodo")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(SRC))
    ap.add_argument("--outdir", default=str(OUT))
    ap.add_argument("--all", action="store_true", help="her istemin tum orneklerini render et")
    ap.add_argument("--frames", type=int, help="kare sinirli (hizli onizleme)")
    args = ap.parse_args()

    src = Path(args.dir)
    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)

    files = sorted(src.glob("*.csv"))
    if not files:
        raise SystemExit(f"CSV yok: {src}  — once import_kimodo.py calistir")

    if not args.all:
        # her istemden sadece ilk ornek
        seen, picked = set(), []
        for f in files:
            tag = f.stem.split("__")[0]
            if tag not in seen:
                seen.add(tag)
                picked.append(f)
        files = picked

    print(f"{len(files)} hareket render edilecek -> {out}/\n")
    ok = 0
    for i, f in enumerate(files, 1):
        mp4 = out / f"{f.stem}.mp4"
        cmd = [sys.executable, "scripts/preview_mujoco.py",
               "--csv", str(f), "--video", str(mp4)]
        if args.frames:
            cmd += ["--frames", str(args.frames)]

        print(f"[{i}/{len(files)}] {f.stem}")
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print(f"    HATA: {r.stderr.strip().splitlines()[-1] if r.stderr else '?'}")
            continue

        # kontak sayfasi
        subprocess.run([sys.executable, "scripts/contact_sheet.py", str(mp4)],
                       capture_output=True)
        ok += 1

    print(f"\n{ok}/{len(files)} render edildi -> {out}/")
    print("Kontak sayfalari ayni klasorde *_sheet.png olarak.")


if __name__ == "__main__":
    main()
