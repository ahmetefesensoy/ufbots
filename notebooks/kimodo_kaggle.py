# ============================================================
# KAGGLE — Kimodo nis dovus sanati denemesi
# ============================================================
# Kaggle'da hazir gelen ornek kodu SIL, bunu yapistir.
# Her bolumu ayri hucre yapabilirsin ya da hepsini tek hucrede calistir.
#
# ONCE SAG PANELDEN:
#   INTERNET     -> ON   (yoksa pip/indirme calismaz)
#   ACCELERATOR  -> GPU T4 x2
# ============================================================


# ---------- 1. Ortam kontrolu ----------
!nvidia-smi --query-gpu=name,memory.total --format=csv
!df -h /kaggle/working | tail -1


# ---------- 2. Kurulum ----------
# Kimodo PyPI'da YOK, GitHub'dan kurulur.
#
# NOT: -q KULLANMA. Kurulum patlarsa asil hatayi gormek gerekiyor;
# sessiz modda "Failed building wheel" disinda bilgi kalmiyor.
#
# Kaggle'in setuptools'u eski olabiliyor -> once guncelle.
!pip install -U pip setuptools wheel

# Wheel build'i ATLA.
# Kaggle'da "Building wheel for kimodo ... did not run successfully /
# No available output" hatasi aliniyor. --no-build-isolation ile paket
# izole ortamda degil, mevcut ortamda kurulur ve wheel adimi atlanir.
# Once bagimliliklari ayri kur (onlar sorunsuz iniyor), sonra kimodo'yu
# bagimliliksiz ekle.
!pip install "hydra-core>=1.3" omegaconf "transformers==5.1.0" peft \
    numpy scipy einops boto3 tqdm "gradio>=5" gradio_client \
    "trimesh>=3.21.7" "scenepic>=1.1.0" "pillow>=9.0" "av>=16.1.0" bvhio \
    "torchao>=0.16.0" accelerate safetensors 2>&1 | tail -5

# kimodo'yu bagimliliklari tekrar cozmeden, build izolasyonu olmadan kur
!pip install --no-build-isolation --no-deps \
    "git+https://github.com/nv-tlabs/kimodo.git" 2>&1 | tail -30

# torchao: Kaggle'da 0.10.0 kurulu ama peft >0.16.0 istiyor.
# Yoksa "ImportError: Found an incompatible version of torchao" ile patlar.
!pip install -U "torchao>=0.16.0" 2>&1 | tail -5

# Kurulum gercekten oldu mu? Buradan sonrasi anlamsizsa hemen dur.
import importlib
import importlib.util
import os
import shutil

cmd_ok = shutil.which("kimodo_gen") is not None
mod_ok = importlib.util.find_spec("kimodo") is not None

print(f"\nkonsol komutu : {'VAR' if cmd_ok else 'YOK'}")
print(f"python modulu : {'VAR' if mod_ok else 'YOK'}")

if not mod_ok:
    # SON CARE: pip'i tamamen atla — repoyu klonla, PYTHONPATH'e ekle.
    # Kimodo saf Python; derleme gerektirmiyor, kaynaktan calisir.
    print("\npip kurulumu tutmadi -> repo klonlanip PYTHONPATH'e ekleniyor")
    import subprocess
    import sys

    subprocess.run(["git", "clone", "--depth", "1",
                    "https://github.com/nv-tlabs/kimodo.git",
                    "/kaggle/working/kimodo_src"], check=False)
    sys.path.insert(0, "/kaggle/working/kimodo_src")
    os.environ["PYTHONPATH"] = "/kaggle/working/kimodo_src"

    importlib.invalidate_caches()
    mod_ok = importlib.util.find_spec("kimodo") is not None
    print("klonlama sonrasi modul:", "VAR" if mod_ok else "YOK")

if not mod_ok:
    print("\n" + "!"*60)
    print("KURULUM BASARISIZ — yukaridaki pip ciktisinda kirmizi hatayi ara.")
    print("!"*60)
    raise SystemExit("kurulum basarisiz")

if not cmd_ok:
    print("Konsol komutu yok -> 'python -m kimodo.scripts.generate' kullanilacak")


# ---------- 3. HF girisi ----------
# Llama-3-8B gated; token sart. READ-ONLY token kullan.
#
# "Save & Run All" modunda interaktif login() CALISMAZ (kutu acilamaz).
# Bu yuzden token Kaggle Secrets'tan okunur:
#   Add-ons -> Secrets -> Add secret
#   Label: HF_TOKEN     Value: <read-only token>
#   "Attach to notebook" isaretli olmali
import os

from huggingface_hub import hf_hub_download, login

try:
    from kaggle_secrets import UserSecretsClient
    token = UserSecretsClient().get_secret("HF_TOKEN")
    login(token=token)
    print("Secrets'tan giris yapildi")
except Exception as e:
    # Interactive modda calisiyorsan buraya duser — elle giris
    print(f"Secret okunamadi ({type(e).__name__}), interaktif girise dusuluyor")
    login()

# Erisim dogrulamasi — burada patlarsa uretim de patlar
hf_hub_download("meta-llama/Meta-Llama-3-8B-Instruct", "config.json")
print("Llama-3 erisimi OK")


# ---------- 4. Test uretimi ----------
# Ilk calistirmada ~16 GB iner (Llama-3 + Kimodo), birkac dakika surer.
import os
import shutil
import subprocess
import sys

# TEK GPU'YA ZORLA — en kritik ayar.
# LLM2Vec.encode() kodunda:  if torch.cuda.device_count() <= 1: <normal dongu>
# else: <multiprocessing.Pool>.  Kaggle T4 x2 verdigi icin ikinci kola giriyor
# ve Kaggle'in kucuk /dev/shm'i yuzunden su hatayla patliyor:
#   RuntimeError: unable to allocate shared memory(shm) ... (11)
# Tek GPU gosterince multiprocessing devre disi kalir.
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

# Metin kodlayici CPU'da kalmali.
# Llama-3 8B tek basina T4'un 15 GB'ini doldurdu ve Kimodo modeline
# 12 MiB bile kalmadi:  "CUDA out of memory ... 6.81 MiB is free"
# CPU'ya alinca VRAM <3 GB'a duser, Kimodo difuzyonu GPU'da kosar.
os.environ["TEXT_ENCODER_DEVICE"] = "cpu"

# Bellek parcalanmasini azalt (hata mesajinin kendi onerisi)
os.environ["PYTORCH_ALLOC_CONF"] = "expandable_segments:True"

# Klonlama yoluna dusulduyse alt surecler de gorebilsin
if os.path.isdir("/kaggle/working/kimodo_src"):
    os.environ["PYTHONPATH"] = "/kaggle/working/kimodo_src"

# konsol komutu yoksa modulu dogrudan cagir
GEN = ["kimodo_gen"] if shutil.which("kimodo_gen") else [sys.executable, "-m", "kimodo.scripts.generate"]

r = subprocess.run(GEN + [
    "a person throws a straight punch",
    "--model", "Kimodo-G1-RP-v1",
    "--duration", "3", "--num_samples", "1", "--seed", "0",
    "--output", "/kaggle/working/out_test/test.csv",
])
print("\ncikis kodu:", r.returncode, "->", "OK" if r.returncode == 0 else "HATA (yukaridaki traceback'e bak)")

!find /kaggle/working/out_test -type f | head


# ---------- 5. Cikti formatini olc ----------
# Kimodo = G1Skeleton34 (34 eklem), BONES-SEED/Menagerie = 29.
# Farki yerelde scripts/import_kimodo.py kapatir.
import glob
import numpy as np
import pandas as pd

for f in sorted(glob.glob("/kaggle/working/out_test/**/*.csv", recursive=True))[:3]:
    d = pd.read_csv(f)
    print(f"{f}\n  satir={len(d)}  kolon={len(d.columns)}")
    print("  ilk 10 kolon:", list(d.columns[:10]))
    num = d.select_dtypes("number")
    birim = "radyan" if num.abs().max().max() < 7 else "derece"
    print(f"  aralik: {num.min().min():.2f} .. {num.max().max():.2f}  -> {birim}\n")

for f in sorted(glob.glob("/kaggle/working/out_test/**/*.npz", recursive=True))[:2]:
    z = np.load(f, allow_pickle=True)
    print(f, "\n  anahtarlar:", list(z.keys()))
    for k in z.keys():
        try:
            print(f"    {k}: {z[k].shape}")
        except Exception:
            pass


# ---------- 6. Nis dovus sanati istemleri ----------
# Her hareketi IKI bicimde soruyoruz:
#   *_named : model stili biliyorsa en iyisini verir
#   *_desc  : bilmiyorsa bile mekanigi tarif ettigimiz icin uretebilir
# Ikisi ayni cikarsa model stili bilmiyor demektir.
# control_boxing = datasette var oldugunu bildigimiz hareket (saglik kontrolu)

PROMPTS = {
    "bokator_named":  "a bokator fighter performs a khmer elbow strike",
    "bokator_desc":   "a fighter steps forward and delivers a downward elbow strike, then recovers to guard",
    "bokator_knee":   "a fighter drives a knee strike upward while pulling both hands down",

    "muaythai_named": "a muay thai fighter throws a roundhouse kick",
    "muaythai_desc":  "a fighter pivots on the left foot and swings the right leg horizontally at head height",

    "spin_named":     "a martial artist performs a spinning back kick",
    "spin_desc":      "a fighter turns 180 degrees on one foot then thrusts the other heel backward, then returns to stance",

    "control_boxing": "a person shadow boxes with alternating straight punches",
}

import glob
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Tek GPU — shm hatasini onler (aciklama 4. bolumde)
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
# Metin kodlayici CPU'da — yoksa Llama-3 VRAM'i doldurup OOM veriyor
os.environ["TEXT_ENCODER_DEVICE"] = "cpu"
os.environ["PYTORCH_ALLOC_CONF"] = "expandable_segments:True"

if os.path.isdir("/kaggle/working/kimodo_src"):
    os.environ["PYTHONPATH"] = "/kaggle/working/kimodo_src"

# kimodo_gen konsol komutu yoksa modulu dogrudan cagir
if shutil.which("kimodo_gen"):
    BASE = ["kimodo_gen"]
else:
    BASE = [sys.executable, "-m", "kimodo.scripts.generate"]
print("komut:", " ".join(BASE))

# NOT: her istem icin ayri surec baslatmak Llama-3'u her seferinde yeniden
# yukluyor (~1 dk). Tek surecte hepsini uretmek daha hizli olurdu ama
# kimodo_gen coklu istemleri NOKTAYLA ayiriyor; bizim istemlerde virgul ve
# nokta var, yanlis bolunme riski yuksek. Bu yuzden tek tek gidiyoruz.
for name, prompt in PROMPTS.items():
    # Zaten uretilmisse atla — oturum kesilirse kaldigi yerden devam eder
    if glob.glob(f"/kaggle/working/out/{name}*"):
        print(f"[atlandi] {name} — zaten var")
        continue

    print(f"\n{'='*65}\n{name}: {prompt}\n{'='*65}", flush=True)
    r = subprocess.run(BASE + [
        prompt,
        "--model", "Kimodo-G1-RP-v1",
        "--duration", "5", "--num_samples", "3", "--seed", "0",
        "--output", f"/kaggle/working/out/{name}.csv",
    ])
    if r.returncode != 0:
        print(f"[HATA] {name} uretilemedi (kod {r.returncode}) — devam ediliyor")

# Ozet: kac tanesi tuttu?
print(f"\n{'='*65}")
uretilen = sorted({Path(p).stem.split('_00')[0] for p in glob.glob('/kaggle/working/out/**/*', recursive=True) if Path(p).is_file()})
print(f"URETILEN: {len(uretilen)}/{len(PROMPTS)}")
for u in uretilen:
    print("  +", u)
eksik = [k for k in PROMPTS if not glob.glob(f"/kaggle/working/out/{k}*")]
if eksik:
    print("EKSIK:", ", ".join(eksik))


# ---------- 7. Ciktiyi paketle ----------
# Kaggle'da google.colab yok. /kaggle/working icindeki dosyalar
# sag paneldeki "Output" sekmesinden indirilir.
!cd /kaggle/working && zip -qr kimodo_out.zip out && du -sh kimodo_out.zip
!ls -la /kaggle/working/kimodo_out.zip

print("""
-----------------------------------------------------------
INDIRME: sag panel -> Output sekmesi -> kimodo_out.zip
(gorunmuyorsa once Save Version ile calistir)

YERELDE:
  python scripts/import_kimodo.py kimodo_out.zip
  python scripts/preview_mujoco.py --csv data/kimodo_csv/<dosya>.csv --video results/x.mp4
  python scripts/contact_sheet.py results/x.mp4
-----------------------------------------------------------
""")
