# RunPod Egitim Rehberi

**Butce: $5 · Tahmini kullanim: $2-3 · Sure: 4-6 saat**

En buyuk risk para degil, **kurulumda zaman kaybetmek**. Bu rehber
sirayla takip edilirse sapma olmaz.

---

## 0. Once bunu oku

| Kural | Sebep |
|---|---|
| **RTX GPU sec** (4090 / A6000 / L40S) | Isaac Sim RT Core istiyor. A100/H100 **desteklenmiyor**. |
| **Volume kullan** (en az 60 GB) | Isaac Sim ~30 GB. Pod silinince volume kalir. |
| **Is bitince pod'u durdur** | Calisirken saat basi odersin. |
| Kurulum bitince **snapshot al** | Ikinci denemede kurulum tekrar etmez. |

---

## 1. Pod olustur

RunPod → **Deploy** → GPU sec:

| GPU | $/saat | Not |
|---|---|---|
| **RTX 4090** | ~0.34 | ✅ en ucuz uygun |
| RTX A6000 | ~0.49 | 48 GB VRAM, daha rahat |
| L40S | ~0.79 | en hizli |

**Template:** `RunPod PyTorch 2.x` (CUDA 12.x)
**Volume:** 60 GB, mount `/workspace`
**Ports:** 8888 (jupyter) yeterli

---

## 2. Baglan ve ortami hazirla

Web terminal ya da SSH:

```bash
cd /workspace
nvidia-smi                      # RTX gorunuyor mu, dogrula
df -h /workspace                # 60 GB var mi
```

`nvidia-smi` cikisinda **RTX** yazmiyorsa pod'u sil, dogru GPU ile ac.

---

## 3. Isaac Sim + Isaac Lab kur

⚠️ **En uzun adim (~30-45 dk).** Sabirli ol, cikti akiyorsa calisiyor.

**Python 3.11 SART** (Isaac Sim 5.x icin):

```bash
python --version            # 3.11.x olmali, degilse:
conda create -n isaac python=3.11 -y && conda activate isaac
```

```bash
cd /workspace
pip install --upgrade pip

# PyTorch — Isaac Sim'in bekledigi tam surum
pip install -U torch==2.7.0 torchvision==0.22.0  --index-url https://download.pytorch.org/whl/cu128

# Isaac Sim 5.1.0
pip install "isaacsim[all,extscache]==5.1.0"  --extra-index-url https://pypi.nvidia.com

# Isaac Lab
git clone https://github.com/isaac-sim/IsaacLab.git
cd IsaacLab
./isaaclab.sh --install
```

Dogrulama:

```bash
python -c "import isaacsim; print('isaacsim OK')"
python -c "import isaaclab; print('isaaclab OK')"
```

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
| Disk dolu | Volume'u 60 GB'a cikar |

---

## Maliyet takibi

RunPod panelinde canli harcama gorunur. Beklenen:

```
kurulum      1.5 saat   $0.51
donusum      0.2 saat   $0.07
deneme       0.3 saat   $0.10
egitim       3.0 saat   $1.02
eval+export  0.5 saat   $0.17
--------------------------------
toplam       5.5 saat   ~$1.87
```

$5 butcede rahat pay var.

---

*Motion Data by Bones Studio*
