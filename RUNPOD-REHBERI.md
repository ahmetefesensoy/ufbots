# RunPod Egitim Rehberi

**Butce: $5 · Tahmini kullanim: $2-3 · Sure: 4-6 saat**

En buyuk risk para degil, **kurulumda zaman kaybetmek**. Bu rehber
sirayla takip edilirse sapma olmaz.

---

## 0. BUTCE KURALLARI — once bunu oku

$5 son butce. Asagidakileri harfiyen uygula, sapma para yakar.

| Kural | Sebep |
|---|---|
| **COMMUNITY CLOUD sec** | Secure Cloud RTX 4090 = $0.69/saat. Community = ~$0.34. **Iki kati fark.** |
| **RTX GPU sec** (4090 / A5000 / A4000) | Isaac Sim RT Core istiyor. A100/H100 **desteklenmiyor**. |
| **Disk 40 GB** (60 degil) | Isaac Sim ~25 GB + checkpoint. 40 yeter. |
| **Isi TEK OTURUMDA bitir** | Pod durdurulunca disk ucreti **ikiye katlaniyor** ($0.20/GB/ay). |
| **Bitince TERMINATE** (Stop degil) | Stop = disk ucreti devam eder. Terminate = her sey durur. |

### Gercek maliyet tablosu

| Senaryo | Community | Secure |
|---|---|---|
| iyi (4h, tek oturum) | **$1.79** ✅ | $3.19 ⚠️ |
| orta (6h, 2 gun bekleme) | **$2.89** ✅ | $4.99 ❌ |
| kotu (9h, 3 gun bekleme) | $4.34 ⚠️ | $7.48 ❌ |

**Secure Cloud'da orta senaryo butceyi asiyor.** Community Cloud sart.

> Community Cloud ucuncu taraf makineler — biraz daha az garantili ama
> bizim isimiz icin fark etmez. Fiyat farki hayati.

### Acil durum freni

RunPod panelinde canli harcama gorunur. **$3.50'yi gecerse** pod'u
hemen terminate et, elindeki checkpoint'le devam et.

---

## 1. Pod olustur

RunPod → **Deploy** → sol ustte **Community Cloud** sekmesini sec.

| GPU | ~$/saat | VRAM | Not |
|---|---|---|---|
| **RTX A4000** | ~0.17 | 16 GB | ✅ en ucuz, yeterli |
| **RTX A5000** | ~0.26 | 24 GB | ✅ rahat |
| RTX 4090 | ~0.34 | 24 GB | en hizli |

> A4000 16 GB — `num_envs=512` ile sorunsuz. Butce daraysa bunu sec.

**Template:** `RunPod PyTorch 2.x` (CUDA 12.x)
**Container disk:** 40 GB
**Volume:** gerekmiyor (tek oturumda bitireceksin)

⚠️ **Volume eklersen** pod'u terminate etsen bile disk ucreti devam eder.
Tek oturum planinda volume'a gerek yok.

---

## 2. Baglan ve ortami hazirla

Web terminal ya da SSH:

```bash
cd /workspace
nvidia-smi                      # RTX gorunuyor mu, dogrula
df -h /workspace                # 40 GB var mi
```

`nvidia-smi` cikisinda **RTX** yazmiyorsa pod'u sil, dogru GPU ile ac.

---

## 3. Isaac Lab — HAZIR IMAJ KULLAN

⚠️ **pip ile kurma!** 45 dakika surer ve para yakar.
NVIDIA'nin hazir imaji var ve **SONIC'in istedigi tam surum**:

```
nvcr.io/nvidia/isaac-lab:2.3.2
```

### Pod olustururken

**Template** yerine **Custom Image** sec ve yukaridaki adresi gir.

Environment variables (zorunlu):
```
ACCEPT_EULA=Y
PRIVACY_CONSENT=Y
```

Bu ikisi olmazsa konteyner acilmaz.

### Baglaninca dogrula

```bash
python -c "import isaaclab; print('isaaclab OK')"
ls /workspace/isaaclab        # bos OLMAMALI
```

> ⚠️ Bilinen sorun: RunPod UDP trafigi acmiyor, bazi durumlarda
> `/workspace/isaaclab/` bos kaliyor. Bos gorursen pod'u terminate
> edip asagidaki alternatife gec.

### Alternatif: pip kurulumu (imaj calismazsa)

Sadece hazir imaj tutmazsa. **Python 3.11 sart.**

```bash
python --version            # 3.11.x olmali
pip install -U torch==2.7.0 torchvision==0.22.0 --index-url https://download.pytorch.org/whl/cu128
pip install "isaacsim[all,extscache]==5.1.0" --extra-index-url https://pypi.nvidia.com
git clone https://github.com/isaac-sim/IsaacLab.git && cd IsaacLab && ./isaaclab.sh --install
```

Bu yol ~45 dk ve ~$0.25 ekstra maliyet demek.

---
## 4. GR00T-WBC kur

```bash
cd /workspace
git lfs install
git clone https://github.com/NVlabs/GR00T-WholeBodyControl.git
cd GR00T-WholeBodyControl
git lfs pull                    # ATLAMA — yoksa sessizce bozuk veri
python check_environment.py
pip install -e "gear_sonic/[training]"
python download_from_hf.py --training     # sonic_release checkpoint
```

---

## 5. Veriyi yukle

Yerelde hazirlanan paket: `dist/ufbots_payload.zip` (3 MB)

**RunPod web arayuzu** → dosya yoneticisi → `/workspace` altina surukle.

Ya da terminalden:

```bash
cd /workspace
# (dosyayi yukledikten sonra)
unzip ufbots_payload.zip -d ufbots
ls ufbots/csv | wc -l        # 32 olmali
ls ufbots/base_csv | wc -l   # 17 taban klibi
```

---

## 6. Veriyi donustur

```bash
cd /workspace/GR00T-WholeBodyControl

# dovus klipleri (30 fps kaynak)
python gear_sonic/data_process/convert_soma_csv_to_motion_lib.py \
    --input /workspace/ufbots/csv \
    --output /workspace/motion_lib/robot \
    --fps 30 --fps_source 30 --individual --num_workers 8

# taban karisimi (BONES-SEED, 120 fps kaynak)
python gear_sonic/data_process/convert_soma_csv_to_motion_lib.py \
    --input /workspace/ufbots/base_csv \
    --output /workspace/motion_lib/robot \
    --fps 30 --fps_source 120 --individual --num_workers 8

# filtre (bizim adlarda elenecek kelime yok, yine de calistir)
python gear_sonic/data_process/filter_and_copy_bones_data.py \
    --source /workspace/motion_lib/robot \
    --dest /workspace/motion_lib/robot_filtered --workers 8

ls /workspace/motion_lib/robot_filtered | wc -l    # ~49 olmali
```

---

## 7. Kisa deneme (once bunu yap!)

**$0.20'lik sigorta.** Hattin ucdan uca calistigini gorur.

```bash
cd /workspace/GR00T-WholeBodyControl
python gear_sonic/train_agent_trl.py \
    +exp=manager/universal_token/all_modes/sonic_release \
    +checkpoint=sonic_release/last.pt \
    num_envs=512 headless=True \
    ++algo.config.num_learning_iterations=200 \
    ++manager_env.commands.motion.motion_lib_cfg.motion_file=/workspace/motion_lib/robot_filtered \
    use_wandb=false
```

Ne izle:
- `throughput/fps` > 500 → GPU calisiyor
- `rewards/total` artiyor mu → ogrenme var
- Hata yoksa → tam egitime gec

---

## 8. Asil egitim

```bash
cd /workspace/GR00T-WholeBodyControl
nohup python gear_sonic/train_agent_trl.py \
    +exp=manager/universal_token/all_modes/sonic_release \
    +checkpoint=sonic_release/last.pt \
    num_envs=1024 headless=True \
    ++algo.config.num_learning_iterations=20000 \
    ++manager_env.commands.motion.motion_lib_cfg.motion_file=/workspace/motion_lib/robot_filtered \
    use_wandb=false > /workspace/train.log 2>&1 &

tail -f /workspace/train.log
```

`nohup ... &` sayesinde terminal kopsa bile egitim devam eder.

**Hedef metrikler** (SONIC dokumanindan):

| Metrik | Iyi |
|---|---|
| `rewards/total` | 3.0+ |
| `rewards/anchor_pos_err` | < 0.15 m |
| `rewards/body_pos_err` | < 0.10 m |
| `throughput/fps` | 1000+ |

Checkpoint'ler her 2000 adimda `logs_rl/TRL_G1_Track/...` altina yazilir.

---

## 9. Degerlendirme + video

```bash
CKPT=$(ls -t logs_rl/TRL_G1_Track/*/model_*.pt | head -1)
echo $CKPT

# metrikler
python gear_sonic/eval_agent_trl.py \
    +checkpoint=$CKPT +headless=True \
    ++eval_callbacks=im_eval ++run_eval_loop=False ++num_envs=128 \
    "+manager_env/terminations=tracking/eval" \
    "++manager_env.commands.motion.motion_lib_cfg.max_unique_motions=512"

# video (submission icin!)
python gear_sonic/eval_agent_trl.py \
    +checkpoint=$CKPT +headless=True \
    ++eval_callbacks=im_eval ++run_eval_loop=False ++num_envs=8 \
    ++manager_env.config.render_results=True \
    "++manager_env.config.save_rendering_dir=/workspace/renders" \
    ++manager_env.config.env_spacing=10.0 \
    "~manager_env/recorders=empty" "+manager_env/recorders=render"
```

**Hedef:** `success_rate > 0.97`, `mpjpe_l < 30 mm`

Bizim PD taban cizgimiz **%0** (32/32 dusuyordu) — bu sayinin ne kadar
yukseldigi calismanin gercek olcusu.

---

## 10. ONNX export (form alani!)

```bash
python gear_sonic/eval_agent_trl.py \
    +checkpoint=$CKPT +headless=True ++num_envs=1 \
    +export_onnx_only=true

ls $(dirname $CKPT)/exported/
```

`*_g1.onnx` → submission'in "ONNX policy" alanina yuklenecek dosya.

---

## 11. Indir ve pod'u durdur

```bash
cd /workspace
tar czf sonuclar.tgz renders/ $(dirname $CKPT)/exported/ train.log
ls -lh sonuclar.tgz
```

Web arayuzunden indir → **pod'u durdur** (Stop, Terminate degil —
volume kalsin ki tekrar kurulum yapmayasin).

---

## Sorun cikarsa

| Belirti | Cozum |
|---|---|
| `isaacsim` import hatasi | RTX olmayan GPU'dasin, pod'u degistir |
| `git lfs pull` atlanmis | Sessiz bozuk veri — tekrar calistir |
| CUDA OOM | `num_envs` dusur (1024 → 512 → 256) |
| Egitim cok yavas | `throughput/fps` bak; <200 ise GPU yanlis |
| Disk dolu | Container disk'i 50 GB'a cikar (pod yeniden olustur) |

---

## Maliyet takibi

RunPod panelinde canli harcama gorunur.

### Hazir imajla (onerilen) — Community Cloud RTX A5000 @ $0.26

```
imaj indirme + acilis    0.3 saat   $0.08
GR00T-WBC kurulum        0.5 saat   $0.13
veri donusumu            0.2 saat   $0.05
kisa deneme (200 iter)   0.3 saat   $0.08
egitim (20000 iter)      3.0 saat   $0.78
eval + render + ONNX     0.5 saat   $0.13
--------------------------------------------
toplam                   4.8 saat   ~$1.25
```

### Pip kurulumuyla (imaj tutmazsa)

```
+ Isaac Sim pip kurulum  0.8 saat   +$0.21
--------------------------------------------
toplam                   5.6 saat   ~$1.46
```

### Guvenlik payi

| Durum | Maliyet | Butce |
|---|---|---|
| Her sey yolunda | ~$1.25 | ✅ $3.75 kalir |
| Bir seyler takilir (2x sure) | ~$2.50 | ✅ $2.50 kalir |
| Felaket (3x sure) | ~$3.75 | ⚠️ $1.25 kalir |

**$3.50 esigini gecerse dur.** Elindeki checkpoint'le devam et —
20000 degil 5000 iterasyonda bile kullanilabilir sonuc cikar.

---

*Motion Data by Bones Studio*
