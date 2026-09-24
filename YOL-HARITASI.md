# Bones Studio Hackathon — Martial Arts Track Yol Haritası

Sıfırdan başlayan biri için, formdaki 7 alanı da dolduracak tam iş planı.

---

## 0. Hedef: formdaki 7 alan

| # | Alan | Nasıl üretilir |
|---|------|----------------|
| 1 | Track | Martial Arts (seçildi) |
| 2 | Project name | Seçtiğin hareketin adı, robot adıyla: `G1 <Hareket Adı>` |
| 3 | Writeup | Ne öğrettin / neden zor / nasıl yaptın |
| 4 | GitHub repo | Fork + training config + scriptler |
| 5 | ONNX policy (HF) | `+export_onnx_only=true` çıktısı → `*_g1.onnx` |
| 6 | Dataset (HF) | Kendi motion setin (Kimodo + BONES-SEED alt kümesi) |
| 7 | Sim video (YouTube) | `render_results=True` çıktısı, before/after kurgu |

**Zorunlu:** Herkese açık paylaşımda `"Motion Data by Bones Studio"` kredisi.

---

## 1. En kritik gerçek: sıfırdan eğitim YOK

NVIDIA dokümanı net: **"64+ GPU öneriyoruz"**, tam yakınsama 100K iterasyon.
Tek node (8 GPU) çalışır ama "kayda değer ölçüde yavaş".

> **Strateji: `sonic_release/last.pt` checkpoint'inden fine-tune.**
> Yarışmanın verdiği şey zaten bu — eğitilmiş bir temel model + onu kendi
> hareketinle uzmanlaştırma imkanı. Kimse sıfırdan eğitmiyor.

Bu, işi "birkaç ay GPU" seviyesinden "birkaç saat fine-tune" seviyesine indiriyor.

---

## 2. Hareket seçimi (ilk ve en stratejik karar)

BONES-SEED'in **Martial Arts kategorisinde sadece 20 hareket** var. Yani
hazır veri havuzu küçük — bu da yarışmanın seni **Kimodo ile kendi hareketini
üretmeye** yönlendirdiği anlamına geliyor.

### Seçim kriterleri
İyi bir yarışma hareketi şu üçünü birden sağlamalı:

1. **Görsel olarak çarpıcı** — jüri videoyu izleyecek
2. **Fizik olarak zor ama imkansız değil** — denge kaybı/dönme içermeli
3. **Before/after farkı net görünmeli** — base policy'nin beceremediği,
   fine-tune sonrası becerdiği bir şey

### Aday hareketler (zorluk sırasıyla)

| Hareket | Zorluk | Neden iyi aday |
|---|---|---|
| Front kick (ön tekme) | Düşük | Garanti çalışır, ama sıradan |
| Roundhouse kick | Orta | Kalça rotasyonu + tek ayak denge |
| **Spinning back kick** | **Yüksek** | **360° dönüş + tek ayak + momentum — formun kendi örneği** |
| Butterfly kick / tornado | Çok yüksek | Havada faz var, G1 için riskli |

> **Öneri: Roundhouse veya spinning back kick.** Formun placeholder'ı
> "G1 Spinning Back Kick" diyor — bu bir ipucu olabilir ama aynı zamanda
> herkesin onu yapacağı anlamına gelir. Roundhouse + belirgin bir varyasyon
> (örn. düşük/yüksek kombinasyon) daha ayırt edici olabilir.

**Filtreleme yaparken işine yarayacak metadata kolonları:**
`content_type_of_movement`, `content_body_position`, `content_uniform_style`

---

## 3. Kurulum (Gün 1)

### 3.1 Hesaplar — HEMEN başlat
- [ ] **Hugging Face hesabı** aç
- [ ] **BONES-SEED lisansını kabul et** → https://huggingface.co/datasets/bones-studio/seed
      ⚠️ Bu **gated** bir dataset; onay beklemesi olabilir. **İlk iş bu olsun.**
- [ ] **Nebius Physical AI** erişimi (yarışma compute kredisi)
- [ ] **GitHub** repo (fork)
- [ ] **W&B** hesabı (training takibi için, opsiyonel ama çok işe yarar)

### 3.2 npa CLI (yerel makine — GPU gerekmez)
```bash
git clone https://github.com/nebius/nebius-physical-ai
cd nebius-physical-ai
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e npa
npa --version
npa configure
npa workbench health preflight --checks nebius --json
```
> Dokümandan: *"Uzak GPU işleri kendi container bağımlılıklarını kullanır;
> CLI için yerel CUDA veya GPU gerekmez."* → Windows makinen yeterli.

### 3.3 GR00T-WBC (Nebius GPU makinesinde)
```bash
git clone https://github.com/NVlabs/GR00T-WholeBodyControl.git
cd GR00T-WholeBodyControl
git lfs pull          # ⚠️ ATLAMA — yoksa sessizce bozuk pointer dosyalar gelir
python check_environment.py
pip install -e "gear_sonic/[training]"
python download_from_hf.py --training
```
Isaac Lab (v2.3.2) ayrıca kurulmalı.

---

## 4. Veri hattı (Gün 2–3)

### 4.1 Hareketi üret/topla — iki kaynağı birleştir

**A) Kimodo ile text-to-motion:** Hareketi metinle üret
("a martial artist performs a spinning back kick"). Çeşitlilik için birden
fazla varyasyon üret — fine-tune'un genellemesi için şart.

**B) BONES-SEED'den ilgili hareketleri çek:** Martial Arts kategorisi (20 hareket)
+ metin açıklamalarıyla arama (her motion'da 6 adede kadar açıklama var).

> **Neden ikisi birden:** Sadece tek bir motion'a fine-tune edersen policy
> aşırı uyum sağlar (catastrophic forgetting) ve robot yürümeyi unutur.
> Hedef hareketi + genel hareket havuzundan bir taban karışımı kullan.

### 4.2 Formatı hazırla
Gereken format: **motion_lib PKL**. BONES-SEED'in `g1/` CSV'leri doğrudan uygun.

```bash
# CSV → PKL
python gear_sonic/data_process/convert_soma_csv_to_motion_lib.py \
    --input /path/to/bones_seed/g1/csv/ \
    --output data/motion_lib_bones_seed/robot \
    --fps 30 --fps_source 120 --individual --num_workers 16

# G1'in yapamayacağı hareketleri ele (~%8.7 gider)
python gear_sonic/data_process/filter_and_copy_bones_data.py \
    --source data/motion_lib_bones_seed/robot \
    --dest data/motion_lib_bones_seed/robot_filtered --workers 16
```
Faydalı bayraklar: `--dry-run` (önizleme), `--add-keywords` (kendi filtren).

Kimodo BVH çıktısı için:
```bash
python gear_sonic/data_process/extract_soma_joints_from_bvh.py \
    --input /path/to/bvh/ --output data/motion_lib_bones_seed/soma \
    --fps 30 --num_workers 16 --skip_existing
```

### 4.3 Eğitimden ÖNCE veriyi gözle doğrula
```bash
python gear_sonic/train_agent_trl.py \
    +exp=manager/universal_token/all_modes/sonic_release \
    ++replay=True num_envs=4 headless=False
```
> Bozuk/kaymış motion ile eğitime başlamak en pahalı hata. Bu adımı atlama.

---

## 5. Eğitim (Gün 3–5)

### 5.1 Önce küçük ölçekte dene (ucuz akıl sağlığı testi)
```bash
python gear_sonic/train_agent_trl.py \
    +exp=manager/universal_token/all_modes/sonic_release \
    num_envs=16 headless=True \
    ++manager_env.commands.motion.motion_lib_cfg.motion_file=sample_data/robot_filtered \
    ++manager_env.commands.motion.motion_lib_cfg.smpl_motion_file=sample_data/smpl_filtered
```
Repo `sample_data/` ile geliyor — hattın uçtan uca çalıştığını burada doğrula.

### 5.2 Asıl fine-tune
```bash
python gear_sonic/train_agent_trl.py \
    +exp=manager/universal_token/all_modes/sonic_release \
    +checkpoint=sonic_release/last.pt \
    num_envs=4096 headless=True \
    ++manager_env.commands.motion.motion_lib_cfg.motion_file=<kendi_veri>/robot_filtered \
    ++manager_env.commands.motion.motion_lib_cfg.smpl_motion_file=<kendi_veri>/smpl_filtered
```
Çok GPU:
```bash
accelerate launch --num_processes=8 gear_sonic/train_agent_trl.py \
    +exp=manager/universal_token/all_modes/sonic_release \
    +checkpoint=sonic_release/last.pt \
    num_envs=4096 headless=True
```

### 5.3 İzlenecek metrikler
| Metrik | Hedef |
|---|---|
| `rewards/total` | 3.0+ |
| `rewards/anchor_pos_err` | < 0.15 m |
| `rewards/body_pos_err` | < 0.10 m |
| `throughput/fps` | ~4000+ |

Checkpoint'ler her 2000 adımda `logs_rl/TRL_G1_Track/...` altına kaydedilir.

**Adaptive sampling kontrolü:** Birkaç yüz iterasyon sonra
`adp_samp/failure_rate_max`, `adp_samp/failure_rate_mean`'den ayrışmalı.
Ayrışmıyorsa hata atfı bozuk demektir.

---

## 6. Değerlendirme + video (Gün 5–6)

### 6.1 Metrikler
```bash
python gear_sonic/eval_agent_trl.py \
    +checkpoint=<path.pt> +headless=True \
    ++eval_callbacks=im_eval ++run_eval_loop=False ++num_envs=128 \
    "+manager_env/terminations=tracking/eval" \
    "++manager_env.commands.motion.motion_lib_cfg.max_unique_motions=512"
```
Hedef: `success_rate` > 0.97, `mpjpe_l` < 30 mm, `mpjpe_g` < 200 mm

### 6.2 Video render (submission videosu buradan çıkıyor)
```bash
python gear_sonic/eval_agent_trl.py \
    +checkpoint=<path.pt> +headless=True \
    ++eval_callbacks=im_eval ++run_eval_loop=False ++num_envs=8 \
    ++manager_env.config.render_results=True \
    "++manager_env.config.save_rendering_dir=/tmp/renders" \
    ++manager_env.config.env_spacing=10.0 \
    "~manager_env/recorders=empty" "+manager_env/recorders=render"
```
Çıktı: `000000.mp4`, `000001.mp4`… 

> ⚠️ **Released checkpoint kullanırken** motion yolu override'ı eklemen gerekir
> (gömülü config'inde NVIDIA'nın iç yolları var):
> `"++manager_env.commands.motion.motion_lib_cfg.motion_file=data/motion_lib_bones_seed/robot_filtered"`
> Kendi checkpoint'inde bu gerekmez.

### 6.3 Before/after kurgusu — **bunu iki kez render et**
Form açıkça *"the move, before and after"* istiyor:
1. **Before:** `sonic_release/last.pt` (base) ile aynı hareketi render et → robot beceremez
2. **After:** kendi fine-tuned checkpoint'inle render et → robot yapar
3. Yan yana kurgula, kısa tut (30–60 sn), metrikleri ekrana bas
4. YouTube'a yükle, açıklamaya **"Motion Data by Bones Studio"** yaz

---

## 7. Paketleme ve submit (Gün 6–7)

### 7.1 ONNX export
```bash
python gear_sonic/eval_agent_trl.py \
    +checkpoint=<path.pt> +headless=True ++num_envs=1 \
    +export_onnx_only=true
```
Çıktı `exported/` klasöründe:

| Dosya | Ne için |
|---|---|
| `*_g1.onnx` | **Robot joint girişi — submission için ana dosya** |
| `*_smpl.onnx` | SMPL poz girişi |
| `*_teleop.onnx` | VR teleop girişi |
| `*_encoder.onnx` / `*_decoder.onnx` | Ayrık parçalar |

→ Hepsini bir HF model repo'suna yükle.

### 7.2 HF dataset repo
Kendi motion setin (Kimodo çıktıları + seçtiğin BONES-SEED alt kümesi)
+ README'de kaynak ve **Bones Studio kredisi**.

### 7.3 GitHub repo içeriği
```
├── README.md              # kredi + nasıl çalıştırılır
├── configs/               # kullandığın exp config / override'lar
├── scripts/               # veri hazırlama + train + export komutların
├── data_prep/             # Kimodo prompt'ların, filtre keyword'lerin
└── results/               # metrikler, W&B linki, eval çıktıları
```

### 7.4 Writeup iskeleti
Form üç şey soruyor — her birine bir paragraf:
1. **Ne öğrettin:** Hareket, neden bu hareket
2. **Neden zor:** Denge, momentum, tek ayak destek fazı, G1'in DOF limitleri,
   base policy'nin nerede başarısız olduğu (before videosuyla destekle)
3. **Nasıl yaptın:** Kimodo ile motion üretimi → retarget → filtre →
   `sonic_release`'den fine-tune → metrikler → ONNX export

---

## 8. Riskler ve dikkat edilecekler

| Risk | Etki | Önlem |
|---|---|---|
| **BONES-SEED lisans onayı gecikir** | Her şey bloke | İlk gün başvur |
| **`git lfs pull` atlanır** | Sessiz bozuk veri | check_environment.py çalıştır |
| **Nebius MuJoCo imajı oynak** | Pipeline durur | Doküman: eski H100 birleşik imaj *karantinada*; mevcut release sadece 64 adımlık kabul testi belgeliyor, uzun yürüyüş garantisi yok → zaman payı bırak |
| **Tek motion'a aşırı uyum** | Robot yürümeyi unutur | Taban hareket karışımı ekle |
| **Kötü veriyle eğitim** | GPU saati çöpe | `++replay=True` ile önce gözle bak |
| **64 GPU yok** | Yavaş yakınsama | Fine-tune + az iterasyon; sıfırdan eğitme |

---

## 9. Özet zaman planı

| Gün | İş |
|---|---|
| 1 | Hesaplar, **lisans başvurusu**, npa + GR00T kurulumu |
| 2 | Hareket seçimi, Kimodo ile motion üretimi |
| 3 | Retarget + filtre + `replay` ile doğrulama, küçük ölçek test |
| 4–5 | Fine-tune, metrik takibi |
| 5–6 | Eval, before/after render, video kurgu |
| 6–7 | ONNX export, HF yüklemeleri, repo, writeup, **submit** |

> Form draft kaydediyor ve kapanışa kadar tekrar tekrar submit edilebiliyor.
> **Elindekilerle erken bir draft kaydet**, sonra iyileştir.

---

## Kaynaklar
- [GR00T-WholeBodyControl](https://github.com/NVlabs/GR00T-WholeBodyControl) · [Docs](https://nvlabs.github.io/GR00T-WholeBodyControl/)
- [SONIC paper (arXiv 2511.07820)](https://arxiv.org/html/2511.07820v1) · [Proje sayfası](https://nvlabs.github.io/GEAR-SONIC/)
- [BONES-SEED dataset](https://huggingface.co/datasets/bones-studio/seed) · [Lisans](https://bones.studio/info/seed-license)
- [Nebius Physical AI](https://github.com/nebius/nebius-physical-ai) · [G1+SONIC guide](https://github.com/nebius/nebius-physical-ai/blob/main/docs/workbench/guides/g1-humanoid-walk-sonic.md)
- [Kimodo](https://github.com/nv-tlabs/kimodo) · [Proje sayfası](https://research.nvidia.com/labs/sil/projects/kimodo)
- [nvidia/GEAR-SONIC (HF)](https://huggingface.co/nvidia/GEAR-SONIC)

*Motion Data by Bones Studio*
