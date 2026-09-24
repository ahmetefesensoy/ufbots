# GPU Secenekleri — Nebius kredisi olmadan

## Kritik kisit: Isaac Sim RT Core istiyor

Isaac Lab/Isaac Sim dokumantasyonu net:

> GPU requirements: RTX series with RT Cores, minimum 12GB VRAM
> (RTX 3080 Ti or better). **A100 and H100 are explicitly NOT supported**
> despite being powerful datacenter GPUs — they lack RT Cores.

Bu sunlari **eler**:

| Platform | GPU | Durum |
|---|---|---|
| Kaggle (bedava) | T4 / P100 | ❌ RT Core yok |
| Colab (bedava) | T4 | ❌ RT Core yok |
| HF ZeroGPU | paylasimli | ❌ 5 dk/gun, RT Core yok |
| Cogu bulut A100/H100 | ❌ | resmen desteklenmiyor |

**Gerekli:** RTX 3080 Ti / 4090 / A6000 / L40S / RTX PRO 6000

---

## Secenek 1 — Nebius Research Grants ⭐ ilk denenecek

Builder Program'i kaciridik ama **arastirma hibesi** ayri bir program:

https://nebius.com/nebius-research-grants

- Arastirmacilara ucretsiz GPU bulut erisimi
- Yarisma zaten Nebius ile ortak — basvuruda bunu belirt
- Ogrenci/bireysel arastirmaci olarak basvurulabilir

**Basvuru metni onerisi:**
> Unitree G1 uzerinde motion tracking calismasi. NVIDIA SONIC/GR00T-WBC
> ile 32 klipllik ozel bir dovus hareketi setini fine-tune edecegim.
> Veri hatti hazir, fizik dogrulamasi yapildi (32/32 klip PD kontrolde
> dusuyor — politika egitimi gerekli oldugunun olcusu). Tahmini ihtiyac:
> tek RTX GPU, 3-5 saat.

---

## Secenek 2 — RunPod (cebden, ucuz) ⭐ en garanti

RTX 4090 saatlik ~$0.34, A6000 ~$0.49.

### Gercekci maliyet

| Is | Sure | Maliyet |
|---|---|---|
| Kurulum (Isaac Lab + GR00T-WBC + checkpoint) | 1-2 saat | ~$0.70 |
| Kisa deneme (2000 iter) | 0.5 saat | ~$0.17 |
| Asil egitim (20000 iter) | 3 saat | ~$1.00 |
| Eval + render + ONNX export | 0.5 saat | ~$0.17 |
| **Toplam** | **5-6 saat** | **~$2** |

Kurulum uzun surerse bile $5'i gecmez. **Tek seferlik bir kahve parasi.**

> Not: kurulum en pahali kisim. Bir kere kurup **volume snapshot**
> alirsan sonraki denemeler dakikalar surer.

---

## Secenek 3 — Ucretsiz kredi programlari

| Program | Miktar | Not |
|---|---|---|
| Google Cloud (yeni hesap) | $300 | L4/L40S var, RT Core ✅ |
| Azure (yeni hesap) | $200 | NVads A10 v5 ✅ |
| Thunder Compute (ogrenci) | $20 | ogrenci e-postasi gerek |
| AWS Activate | $1000+ | startup basvurusu |
| Lightning.ai | aylik bedava saat | GPU tipi degisken |

**Google Cloud $300** en pratik: L4 GPU saatlik ~$0.70, RT Core var,
300 dolar bizim icin fazlasiyla yeter.

---

## Secenek 4 — Egitimsiz submit (son care)

Egitim olmadan da gonderilebilir ama **zayif kalir**:

| Form alani | Egitimsiz |
|---|---|
| GitHub repo | ✅ tam |
| Dataset (HF) | ✅ 32 klip, puanlanmis |
| Writeup | ✅ guclu (fizik bulgusu) |
| **ONNX policy** | ❌ **yok** |
| **Sim video (before/after)** | ⚠️ sadece "before" |

ONNX alani bos kalirsa form "Fill every field to submit" diyor —
**submit edilemeyebilir.**

---

## Onerilen sira

```
1. Nebius Research Grants'a basvur        (bedava, 1-3 gun)
2. Paralel: Google Cloud $300 hesabi ac   (bedava, aninda)
3. Ikisi de olmazsa RunPod'dan ~$2 harca  (garanti)
```

Ucu de olmazsa egitimsiz submit — ama ONNX alani sorun cikarabilir.

---

## Egitim icin hazir olanlar

```
sonic_input/csv/          32 klip, BONES-SEED kolon duzeni
sonic_input/motion_lib/   dogrudan PKL
scripts/train_sonic.sh    5 adimli hat (convert/replay/train/eval/export)
scripts/setup_nebius.sh   GR00T-WBC kurulumu
```

Ayrica taban karisimi (yurume/durus/denge) indiriliyor — robot
sadece dovuse fine-tune edilirse yurumeyi unutur.

### Onerilen ilk kosu

```bash
bash scripts/setup_nebius.sh
bash scripts/train_sonic.sh convert
bash scripts/train_sonic.sh replay      # gozle dogrula (bedava)
NUM_ENVS=1024 ITERS=2000 bash scripts/train_sonic.sh train   # kisa deneme
```

2000 iterasyon yakinsama icin yetmez ama **hattin calistigini** gosterir.
Metrikler dogru yonde giderse tam egitime gec.

---

*Motion Data by Bones Studio*
