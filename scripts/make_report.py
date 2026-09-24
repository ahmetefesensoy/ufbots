"""Veri seti kalite raporu uretir (submission icin).

manifest.json + klip metriklerinden Markdown rapor + grafik cikarir.
Yarisma writeup'inda ve HF dataset kartinda kullanilir.

Kullanim:
    python scripts/make_report.py
    python scripts/make_report.py --out results/DATASET_RAPORU.md
"""
import argparse
import json
from collections import Counter
from pathlib import Path

CURATED = Path("C:/ufbots_tools/data/g1_curated")


def family(stem: str) -> str:
    for f in ("chanleak", "dum_chanleak", "knee_combo", "seah"):
        if stem == f:
            return "kombinasyon"
    for f in ("jump_spin_kick", "jump_kick", "front_kick", "knee_strike",
              "punch_kick_combo", "attack_sequence", "punch", "kick", "spin"):
        if stem.startswith(f):
            return f
    return "diger"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default=str(CURATED / "manifest.json"))
    ap.add_argument("--out", default="results/DATASET_RAPORU.md")
    ap.add_argument("--plot", default="results/dataset_kalite.png")
    args = ap.parse_args()

    mf = Path(args.manifest)
    if not mf.exists():
        raise SystemExit(f"{mf} yok — once curate_dataset.py")
    data = json.loads(mf.read_text(encoding="utf-8"))
    rows = data["kliplar"]
    train = [r for r in rows if r["grup"] == "train"]

    fam = Counter(family(r["klip"]) for r in train)
    sure = sum(r["kare"] for r in train) / 30

    L = []
    L.append("# G1 Bokator — Veri Seti Raporu\n")
    L.append(f"**{len(train)} klip · {sure:.0f} saniye · 30 fps · Unitree G1 29-DOF**\n")
    L.append("Kaynak: CMU Mocap → AMASS SMPL-X → GMR retarget → G1\n")

    L.append("\n## Kalite sureci\n")
    L.append("| Asama | Klip |\n|---|---|")
    L.append(f"| CMU katalogunda dovus hareketi | 35 |")
    L.append(f"| Eklem-farkindali kesme sonrasi | 29 |")
    L.append(f"| Kombinasyon kurma | +4 |")
    L.append(f"| Yumusatma + limit kirpma | 33 |")
    L.append(f"| **Kalite esigini gecen** | **{len(train)}** |")
    rej = [r for r in rows if r["grup"] != "train"]
    if rej:
        L.append(f"| Elenen / incelenecek | {len(rej)} |")

    L.append("\n## Hareket ailesi dagilimi\n")
    L.append("| Aile | Klip | Toplam agirlik |\n|---|---|---|")
    for f, n in fam.most_common():
        w = sum(r["agirlik"] for r in train if family(r["klip"]) == f)
        L.append(f"| `{f}` | {n} | {w:.1f} |")

    L.append("\n## En yuksek puanli klipler\n")
    L.append("| Klip | Puan | Diz | Sicrama | Dik% | Agirlik |\n|---|---|---|---|---|---|")
    for r in sorted(train, key=lambda r: -r["puan"])[:10]:
        L.append(f"| `{r['klip']}` | {r['puan']:.0f} | {r['diz']:.0f}° | "
                 f"{r['sicrama']:.2f} | {r['dik']:.0f}% | {r['agirlik']:.2f} |")

    L.append("\n## Imza hareketler\n")
    sig = [r for r in train if r["agirlik"] >= 1.5]
    L.append("Egitimde daha sik orneklenen klipler (agirlik ≥ 1.5):\n")
    L.append("| Klip | Agirlik | Diz acisi | Sicrama |\n|---|---|---|---|")
    for r in sorted(sig, key=lambda r: -r["agirlik"]):
        L.append(f"| `{r['klip']}` | **{r['agirlik']:.2f}** | {r['diz']:.0f}° | {r['sicrama']:.2f} |")

    L.append("\n## Olcum tanimlari\n")
    L.append("- **dik%** — govde-yukari vektorunun z bileseni > 0.8 olan kare orani")
    L.append("- **sicrama** — kalca yuksekligi / medyan (1.0 = hic havalanma yok)")
    L.append("- **jitter** — eklem acisinin ikinci farkinin ortalamasi (titreme)")
    L.append("- **puan** — dik%(40) + jitter(25) + cokme(20) + genlik(15)")

    L.append("\n## Bilinen sinirlar\n")
    L.append("- Kaynak veri jenerik dovus mocap'i; **bokator'un kendisi degil**")
    L.append("- Dirsek vurusu (Dum) dolayli — yuksek dirsek acisi yumruktan geliyor")
    L.append("- Gures/atis hatti kismi calisiyor (IK karelerin %53'unde cokuyor)")
    L.append("- Ucan teknikler kinematik olarak dogru, fizik egitiminde tutmayabilir")

    L.append("\n---\n\n*Motion Data by Bones Studio*")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L), encoding="utf-8")
    print(f"rapor -> {out}")

    # grafik
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 2, figsize=(13, 5))
        s = sorted(train, key=lambda r: r["puan"])
        ax[0].barh([r["klip"] for r in s], [r["puan"] for r in s], color="#4a7ab8")
        ax[0].set_title("Kalite puani"); ax[0].tick_params(labelsize=6)
        ax[0].axvline(data["min_score"], color="crimson", ls="--", lw=1)
        ax[1].scatter([r["sicrama"] for r in train], [r["diz"] for r in train],
                      s=[r["agirlik"] * 60 for r in train], alpha=.65, color="#c8553d")
        for r in train:
            if r["agirlik"] >= 1.8:
                ax[1].annotate(r["klip"][:16], (r["sicrama"], r["diz"]), fontsize=6)
        ax[1].set_xlabel("sicrama (havada faz)"); ax[1].set_ylabel("diz acisi (derece)")
        ax[1].set_title("Hareket genligi — nokta buyuklugu = egitim agirligi")
        plt.tight_layout(); plt.savefig(args.plot, dpi=110)
        print(f"grafik -> {args.plot}")
    except Exception as e:
        print(f"grafik atlandi: {type(e).__name__}")


if __name__ == "__main__":
    main()
