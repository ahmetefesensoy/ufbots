"""CMU Mocap'tan dovus hareketlerini indirir.

CMU veritabani lisans ucretsiz ve kisitlamasiz. BVH donusumu
(cgspeed / Bruce Hahne) su aynadan aliniyor:
    https://github.com/una-dinosauria/cmu-mocap

Katalog taranarak secilen denekler (bkz. HIBRIT-DOVUS-PLANI.md):

    144  punching female         Front_Kicking, Punch_Sequence, Spin_reach
    135  Martial Arts Walks      Front Kick
     86  sports/various          "knee kicking", kicking, punching
     87  acrobatics              "Jump with kick and spin"
     88  acrobatics              "jump and spin kick", spin kicks
     75  jumps                   jump kick
     90  cartwheels/acrobatics   jump kick
     76  avoidance               "attack with a punch", "avoid attacker"
     74  kicks                   kick, jump kick
    143  general                 Punching, Kicking
    141  general                 Punch and Kick

Kullanim:
    python scripts/fetch_cmu.py                  # varsayilan set
    python scripts/fetch_cmu.py --subjects 144 135
    python scripts/fetch_cmu.py --list           # indirmeden listele
"""
import argparse
import json
import ssl
import urllib.request
from pathlib import Path

REPO = "una-dinosauria/cmu-mocap"
RAW = f"https://raw.githubusercontent.com/{REPO}/master/data"
API = f"https://api.github.com/repos/{REPO}/contents/data"
OUT = Path("data/cmu_bvh")

# Katalog taramasindan cikan dovus icerikli denekler
DEFAULT = {
    "144": "punching female — Front_Kicking, Punch_Sequence, Spin_reach",
    "135": "Martial Arts Walks — Front Kick",
    "086": "sports — kicking, punching, KNEE KICKING",
    "087": "acrobatics — Jump with kick and spin",
    "088": "acrobatics — jump and spin kick",
    "075": "jumps — jump kick",
    "090": "cartwheels/acrobatics — jump kick",
    "076": "avoidance — attack with a punch",
    "074": "kicks — kick, jump kick",
    "143": "general — Punching, Kicking",
    "141": "general — Punch and Kick",
}

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE


def api_get(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "ufbots"})
    return json.load(urllib.request.urlopen(req, context=CTX, timeout=60))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subjects", nargs="+", help="denek numaralari (orn. 144 135)")
    ap.add_argument("--outdir", default=str(OUT))
    ap.add_argument("--list", action="store_true", help="indirme, sadece listele")
    args = ap.parse_args()

    subs = args.subjects or list(DEFAULT)
    # 86 -> 086 normalize
    subs = [s.zfill(3) for s in subs]

    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)

    total = 0
    for s in subs:
        desc = DEFAULT.get(s, "")
        try:
            files = api_get(f"{API}/{s}")
        except Exception as e:
            print(f"S{s}: LISTELENEMEDI ({type(e).__name__})")
            continue

        bvhs = [f for f in files if f["name"].endswith(".bvh")]
        size = sum(f["size"] for f in bvhs) / 1024 / 1024
        print(f"\nS{s}  {len(bvhs)} dosya, {size:.1f} MB  {desc}")

        if args.list:
            for f in bvhs[:5]:
                print(f"     {f['name']}")
            if len(bvhs) > 5:
                print(f"     ... +{len(bvhs)-5}")
            total += len(bvhs)
            continue

        for f in bvhs:
            dest = out / f"cmu_{s}_{f['name']}"
            if dest.exists():
                continue
            req = urllib.request.Request(f["download_url"], headers={"User-Agent": "ufbots"})
            dest.write_bytes(urllib.request.urlopen(req, context=CTX, timeout=180).read())
            print(f"     {dest.name}  ({f['size']/1024:.0f} KB)")
            total += 1

    print(f"\n{'listelendi' if args.list else 'indirildi'}: {total} dosya")
    if not args.list:
        print(f"konum: {out}/")
        print("\nSonraki adim: GMR ile G1'e retarget (bkz. HIBRIT-DOVUS-PLANI.md)")


if __name__ == "__main__":
    main()
