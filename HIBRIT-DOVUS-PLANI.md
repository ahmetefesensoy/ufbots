# G1 Hibrit Dovus Sistemi — Veri Plani

**Fikir:** Tek bir stili taklit etmek yerine, bokator (dirsek/diz/gures) +
muay thai (clinch, diz) + gures (takedown) ogelerini birlestiren,
**G1 icin tasarlanmis** bir dovus sistemi.

Bu yarisma icin daha guclu: "var olan stili kopyaladim" degil,
"robot icin yeni bir dovus dili tasarladim".

---

## 1. FILTRE MESELESI — COZULDU

Onceki uyarim yanlisti. `filter_and_copy_bones_data.py` kaynak kodunu okudum:

```python
def should_filter_out(filename, filter_keywords, include_keywords=None):
    filename_lower = filename.lower()
    return any(keyword.lower() in filename_lower for keyword in filter_keywords)
```

**Sadece DOSYA ADINA bakiyor.** Fizik analizi, denge kontrolu, akrobasi
tespiti yok. Varsayilan 35 anahtarin tamami mobilya/yukseklik adlari:

```
sitting, table, ladder, scooter, stair, box_jump, handstand, cartwheel,
on_1m, off_1m, fall_from, safety_roll, monkey_jump, walking_on_edge, ...
```

Test sonucu:

| Dosya adi | Sonuc |
|---|---|
| `flying_knee` | **GECER** |
| `wrestling`, `takedown`, `grapple`, `clinch` | **GECER** |
| `elbow_strike`, `spin_kick`, `knee_strike` | **GECER** |
| `cartwheel_kick` | ELENIR (`cartwheel` yuzunden) |

**Ucan diz ve gures zaten elenmiyor.** Dosya adlarinda yukaridaki
kelimeleri kullanmazsan hepsi gecer.

Filtreyi tamamen kapatmak istersen:
```bash
python gear_sonic/data_process/filter_and_copy_bones_data.py \
    --source <src> --dest <dst> --filter_keywords ""
```

> ⚠️ Ayri mesele: filtre engel degil ama **G1 fiziksel olarak** ucan dizi
> ogrenmekte zorlanir (havada faz, inis darbesi). Veri akar, egitim zor.
> Bunu writeup'ta durustce anlatmak guclu bir nokta olur.

---

## 2. VERI KAYNAKLARI (arastirma sonucu)

### A. CMU Mocap — ⭐ EN IYI BASLANGIC

**Lisans ucretsiz, kisitlama yok.** BVH hazir:
https://github.com/una-dinosauria/cmu-mocap

Katalogu tarayip dovus iceren trial'lari cikardim:

| Denek | Aciklama | Ise yarayan |
|---|---|---|
| **144** | punching female | Front_Kicking, Left_Punch_Sequence, Punch_Sequence, Spin_reach (34 dosya) |
| **135** | **Martial Arts Walks** | Front Kick (11 dosya) |
| **86** | sports/various | **"walking, running, kicking, punching, knee kicking"** (15 dosya) |
| **87** | acrobatics | **"Jump with kick and spin"** |
| **88** | acrobatics | **"jump and spin kick"**, spin kicks |
| **75** | jumps | **jump kick** |
| **90** | cartwheels/acrobatics | **jump kick** |
| **76** | avoidance | "walk backwards then attack with a punch", "avoid attacker" |
| **74** | kicks | kick, jump kick |
| **143** | general | Punching, Kicking |
| **141** | general | Punch and Kick |

**Dogrulandi:** `144_01.bvh` indirildi — 31 eklem, 2460 kare, 120 fps,
standart CMU iskeleti (SOMA degil).

### B. Motion-X — kung fu alt kumesi

1000+ kung fu klibi, SMPL-X formatinda (GMR'ye dogrudan beslenir).
Lisans **CC BY-NC-SA** (ticari degil), Google Form ile erisim.
https://motion-x-dataset.github.io/

### C. ReMoCap — ⭐ GURES/NINJUTSU

275.7K kare, iki kisilik Ninjutsu + Lindy Hop. Max Planck.
https://vcai.mpi-inf.mpg.de/projects/remos/

### D. Harmony4D — gures (dogrudan)

NeurIPS 2024. Kendi tanimi: *"...during **wrestling** or dancing"*.
Vahsi ortamda yakin temas, iki kisi.

### E. Diger

- **MADS** (Tai-chi, Karate) 53K kare — http://visal.cs.cityu.edu.hk/research/mads/
- **UMONS-TAICHI** 2200 dizi, 13 teknik
- **Kyokushin Karate** (Nature Sci Data) — optik mocap
- **Mixamo** — hazir dovus animasyonlari, Adobe sartlari artik izin verici

---

## 3. BORU HATTI

CMU BVH **SOMA iskeleti degil**, o yuzden NVIDIA'nin soma-retargeter'i
kabul etmez. Iki secenek:

```
SECENEK 1 (CMU icin):
  CMU BVH → SMPL fit → GMR → G1 CSV → PKL → SONIC

SECENEK 2 (video icin):
  video → GVHMR → SMPL → GMR → G1 CSV → PKL → SONIC
```

**GMR** her ikisinde de ortak halka:
https://github.com/YanjieZe/GMR (ICRA 2026, CPU'da gercek zamanli, herhangi URDF)

---

## 4. HIBRIT SISTEM — hareket repertuari

| Kategori | Kaynak | G1'de |
|---|---|---|
| **Dirsek vurusu** (bokator Dum) | video / kendi cekim | ✅ kol hareketi |
| **Ayakta diz** (muay thai) | CMU S86 "knee kicking" | ⚠️ denge |
| **Ucan diz** | CMU S75/S90 jump kick + video | ❌ zor ama veri var |
| **Clinch** (muay thai) | ReMoCap Ninjutsu | ⚠️ iki kisi → tek kisiye ayir |
| **Takedown/gures** | Harmony4D, ReMoCap | ❌ yere inme, cok zor |
| **Spin kick** | CMU S87/S88 | ⚠️ denge |
| **Duruslar** | CMU S135 Martial Arts Walks | ✅ |
| **Yumruk serisi** | CMU S144, BONES-SEED shadow_boxing | ✅ dogrulandi |

---

## 5. ONERILEN SIRA

### Faz 1 — zinciri kanitla (1-2 gun)
CMU S144 (punch/kick) + S135 (martial arts walks) indir
→ GMR ile G1'e retarget → MuJoCo'da izle → PKL'e cevir

**Amac:** boru hattinin uctan uca calistigini gormek. Egitim yok.

### Faz 2 — repertuari genislet
S86 (knee kicking), S87/S88 (spin kick), S75/S90 (jump kick) ekle
→ her birini gozle dogrula, kotuleri ele

### Faz 3 — nis ogeler
- Bokator dirsek/diz: kendi cekimin veya YouTube (GVHMR)
- Gures/clinch: ReMoCap veya Harmony4D (iki kisiden tek kisi ayir)

### Faz 4 — taban karisimi + egitim
BONES-SEED'den yurume/denge hareketleri ekle (SART — yoksa robot
yurumeyi unutur) → `sonic_release`'den fine-tune

---

## 6. NE KADAR VERI

SONIC makalesinde net minimum yok. Referans: bir gorev icin 300 teleop
trajektorisi ile %95 basari.

Bizim icin:
- **Minimum:** 20-30 temiz klip
- **Rahat:** 100+
- **Kritik:** cesitlilik > miktar

CMU'dan sadece listelenen deneklerle ~100 dosya cikar — yeterli baslangic.

---

## 7. DURUST RISK TABLOSU

| Risk | Gercek |
|---|---|
| Ucan diz G1'de calismayabilir | Yuksek ihtimal. Veri akar, egitim zor. |
| Gures/yere inme | Cok dusuk sans. G1 yere inip kalkamaz. |
| CMU iskeleti → SMPL fit | Ekstra adim, kalite kaybi olabilir |
| Iki kisilik veriden tek kisi | ReMoCap/Harmony4D'de ayirma gerekir |
| Motion-X lisansi | CC BY-NC-SA — ticari kullanim yok |

**Oneri:** ucan diz ve guresi hedefe koy ama **writeup'ta hangisinin
tuttugunu hangisinin tutmadigini durustce yaz**. Juri icin "denedim,
su yuzden olmadi" anlatimi, basarisizligi gizlemekten daha degerli.

---

## Kaynaklar

- [CMU Mocap BVH](https://github.com/una-dinosauria/cmu-mocap) — ucretsiz
- [CMU katalog](http://mocap.cs.cmu.edu/search.php)
- [GMR](https://github.com/YanjieZe/GMR) — SMPL-X → G1
- [GVHMR](https://github.com/zju3dv/GVHMR) — video → SMPL
- [Motion-X](https://motion-x-dataset.github.io/) — kung fu
- [ReMoCap/ReMoS](https://vcai.mpi-inf.mpg.de/projects/remos/) — Ninjutsu
- [MADS](http://visal.cs.cityu.edu.hk/research/mads/) — Tai-chi/Karate

*Motion Data by Bones Studio*

---

# DURUM GUNCELLEMESI — 2026-09-22

## Tamamlanan

| Adim | Sonuc |
|---|---|
| CMU BVH indirme | ✅ **239 dosya, 273 MB** — `data/cmu_bvh/` |
| Trial aciklamalari | ✅ 241 kayit — `data_prep/cmu_trials.json` |
| Dovus secimi | ✅ **35 hareket** — `data/combat_bvh/` (63 MB) |

### Secilen repertuar

| Kategori | Adet | Not |
|---|---|---|
| `jump_kick` | **6** | ucan diz/tekme temeli |
| `punch` | 6 | S144 punch sequence |
| `kick` | 5 | S74 |
| `spin` | 5 | S144 spin_reach |
| `front_kick` | 5 | S135 martial arts + S144 |
| `attack_sequence` | 3 | S76 "attack with punch", "avoid attacker" |
| `punch_kick_combo` | 2 | S141, S143 |
| `jump_spin_kick` | **2** | S87 "jump with kick and spin", S88 |
| `knee_strike` | **1** | S86 "knee kicking" — muay thai diz |

Dosya adlari bilerek temiz tutuldu (`cartwheel`, `handstand`, `box_jump`
gibi kelimeler yok) — NVIDIA filtresine takilmasinlar diye.

## RETARGET YOLU — onemli bulgu

GMR'nin BVH destegi **sadece belirli formatlar** icin: `lafan1`, `nokov`,
`xsens`. **CMU formati desteklenmiyor.**

Ama GMR **SMPL-X → unitree_g1** destekliyor (✅ resmi tabloda).

Ve **AMASS'ta CMU'nun hazir SMPL-X versiyonu var** — yani BVH'yi elle
donusturmeye gerek yok:

```
AMASS/CMU (SMPL-X npz)  →  GMR  →  G1  →  PKL  →  SONIC
```

### AMASS erisimi
- https://amass.is.tue.mpg.de/ — kayit + akademik lisans onayi gerekiyor
- CMU alt kumesi `*_poses.npz` olarak iniyor
- SMPL-X N (neutral) formati secilmeli

> Indirdigimiz BVH'ler yine de degerli: hangi trial'in hangi hareket
> oldugunu bulmak ve MuJoCo'da on izleme icin kullanilabilir.

## Sonraki adimlar

1. **AMASS hesabi ac**, CMU alt kumesini indir (SMPL-X N)
2. Sectigimiz 35 trial'a karsilik gelen npz'leri ayikla
3. GMR kur: `pip install -e .` + SMPL-X body model
4. `python scripts/smplx_to_robot.py --robot unitree_g1 ...`
5. MuJoCo'da gozle dogrula (`preview_mujoco.py`)
6. PKL'e cevir, taban karisimi ekle, fine-tune

## Alternatif (AMASS beklemeden)

BVH'leri dogrudan MuJoCo'da on izleyip hangilerinin ise yaradigini
simdiden secebiliriz — retarget olmadan da hareketin kalitesi gorulur.

---

# BVH ON ELEME — AMASS beklerken yapildi

## Sorun: ortalama yaniltiyor

Ilk analizde 23 klip "DURGUN" cikti. Sebep: CMU klipleri uzun ve karisik.
83 saniyelik dosyada diz vurusu sadece 3 saniye — ortalama hareketlilik
dusuk gorunuyor ama vurus var.

Olcum: `knee_strike_086_06` -> ort=0.20, **tepe(1sn)=0.46** (2.3 kat fark)

**Cozum:** ortalama yerine 1 saniyelik kayan pencerenin tepesi.

## Sonuc: 35 klip analiz edildi

| Durum | Adet | Anlam |
|---|---|---|
| UYGUN | 20 | ayakta, dengeli, vurus var |
| **HAVADA** | **9** | sicrama > %18 — **ucan teknikler** |
| DURGUN | 6 | hicbir aninda vurus yok |

`sicrama` = kalca yuksekligi / medyan. 1.41 = havada ciddi faz var.

### Havada faz sıralamasi (ucan diz adaylari)

| Klip | sicrama | tepe |
|---|---|---|
| `jump_kick_075_16` | **1.41** | 1.15 |
| `jump_kick_090_05` | 1.33 | 0.92 |
| `punch_086_05` | 1.31 | 0.49 |
| `jump_kick_090_06/07` | 1.28 | 0.91 |
| `jump_spin_kick_088_06` | 1.25 | **1.52** |

## Kesme: 714 s -> 108 s

`analyze_bvh.py` her klipte vurusun **kacinci saniyede** oldugunu buluyor
(`tepe_s`). `trim_bvh.py` o ani merkez alip 4 saniyelik pencere kesiyor.

Ornekler:
```
knee_strike_086_06    82.8s -> 4.0s  (tepe 36.3s)
punch_kick_combo_086  76.7s -> 4.0s  (tepe 74.6s)
jump_kick_086_03      70.0s -> 4.0s  (tepe 18.5s)
```

**Dogrulama:** kesim sonrasi DURGUN kategorisi **6 -> 0**. Tum klipler
UYGUN (19) veya HAVADA (10). Dolgu atildi, vurus korundu.

Cikti: `data/combat_trimmed/` — 29 klip, 108 saniye

## Neden onemli

Egitime 83 saniyelik klip vermek zararli: robot 80 saniye yurumeyi,
3 saniye vurmayi ogrenir. Kisa ve yogun klipler fine-tune icin cok daha iyi.

## Yeni scriptler

| Script | Is |
|---|---|
| `analyze_bvh.py` | BVH metrikleri + G1 uygunluk puani |
| `trim_bvh.py` | vurus anina gore kesme |

```bash
python scripts/analyze_bvh.py --csv data_prep/bvh_analiz.csv
python scripts/trim_bvh.py --window 4
```

---

# AMASS + GMR KURULUMU — 2026-09-23

## AMASS CMU islendi

`CMU.tar.bz2` (3.15 GB) indirildi. Tumunu acmadan sadece sectigimiz
29 klibin SMPL-X karsiligi cikarildi.

| Adim | Sonuc |
|---|---|
| Arsivden cikarma | ✅ **29/29 klip** — `data/amass_combat/` |
| Vurus anina gore kesme | ✅ **119 s, 30 MB** — `data/amass_trimmed/` |

### Veri formati (dogrulandi)

```
surface_model_type : smplx
gender             : neutral
mocap_frame_rate   : 120.0
poses              : (N, 165)
trans              : (N, 3)
root_orient        : (N, 3)
pose_body          : (N, 63)
betas              : (16,)
```

Tam GMR'nin bekledigi format.

### Kesme ornekleri

```
knee_strike_86_06      82.8s -> 4.0s  (tepe 36.3s)
punch_kick_combo_86_08 76.7s -> 4.0s  (tepe 74.6s)
jump_kick_86_03        70.0s -> 4.0s  (tepe 18.5s)
```

BVH tarafindaki `tepe_s` degerleri kullanildi — iki veri yolu ayni
hareketleri gosteriyor.

## GMR kuruldu

`tools/GMR/` — ICRA 2026, SMPL-X → herhangi humanoid.

### Windows'ta iki engel cikti

**1. Turkce Windows kodlamasi (cp1254)**
`setup.py` README'yi okurken patliyor:
```
UnicodeDecodeError: 'charmap' codec can't decode byte 0x81
```
Cozum: `PYTHONUTF8=1` ile kur.

**2. proxsuite Windows'ta derlenmiyor**
`qpsolvers[proxqp]` bagimliligi C++ derleme istiyor, Windows tekerlegi yok.

Cozum: proxqp yerine Windows uyumlu cozuculer:
```bash
pip install "qpsolvers[quadprog,osqp]"    # proxqp yerine
pip install -e . --no-deps                 # GMR'yi bagimliliksiz kur
```

Kurulu cozuculer: `clarabel, daqp, highs, osqp, quadprog, scs` — yeterli.

### Hazir olanlar

```
tools/GMR/assets/unitree_g1/g1_mocap_29dof.xml     ✅ robot tanimi
tools/GMR/scripts/smplx_to_robot_dataset.py        ✅ toplu retarget
tools/GMR/scripts/batch_gmr_pkl_to_csv.py          ✅ PKL -> CSV
```

## SON EKSIK: SMPL-X body model

GMR insan vucut modelini gerektiriyor (AMASS sadece hareket verisi).

**Indirilecek:** https://smpl-x.is.tue.mpg.de/ → kayit + lisans → Download

Gereken dosya:
```
tools/GMR/assets/body_models/smplx/SMPLX_NEUTRAL.pkl
```
(FEMALE/MALE opsiyonel — verimiz `gender: neutral`)

Bu gelince retarget komutu:
```bash
cd tools/GMR
python scripts/smplx_to_robot_dataset.py \
    --src_folder ../../data/amass_trimmed \
    --tgt_folder ../../data/g1_retargeted \
    --robot unitree_g1
```

## SMPL-X model dosyasi — YANLIS PAKET

`smplx_locked_head.tar.bz2` (791 MB) indirildi ama icerigi **SMPL**,
SMPL-X degil. Icerik incelemesi:

```
neutral/model.pkl  -> 13 anahtar
el/PCA anahtari    -> YOK (hands_componentsl eksik)
```

Gercek SMPL-X'te 20+ anahtar ve `hands_componentsl` olmali.
Hata: `AttributeError: 'Struct' object has no attribute 'hands_componentsl'`

Bu paket ("SOMA/MoSh/AMASS codebase" dugmesi) AMASS'in kendi ic
boru hatti icin; smplx Python kutuphanesi icin degil.

**DOGRUSU:** ilk dugme — *"Download SMPL-X v1.1 (NPZ+PKL, 830 MB) —
Use this for SMPL-X Python codebase"*

Dosya adlari `SMPLX_NEUTRAL.npz` / `SMPLX_NEUTRAL.pkl` olmali
(`model.npz` degil).

---

# RETARGET CALISTI — 2026-09-23

## Dogru SMPL-X paketi

`models_smplx_v1_1.zip` (830 MB) — 1. dugme, "SMPL-X Python codebase".

Dogrulama:
```
SMPLX_NEUTRAL.pkl   519 MB   21 anahtar
hands_componentsl   VAR  ✅
```
(Onceki yanlis paket: 13 anahtar, el bileseni yok.)

## Windows engelleri — hepsi cozuldu

| # | Engel | Cozum |
|---|---|---|
| 1 | Turkce kodlama (cp1254) setup.py'yi patlatiyor | `PYTHONUTF8=1` |
| 2 | `proxsuite` Windows'ta derlenmiyor | `qpsolvers[quadprog,osqp]` + `--no-deps` |
| 3 | `chumpy` kurulumu (setup.py `pip` import ediyor) | `--no-build-isolation` |
| 4 | `chumpy` Py3.12 uyumsuz (`inspect.getargspec`, `np.bool`) | kaynak yamasi (yedekli) |
| 5 | `smplx` NPZ ariyor ama PKL lazim | `ext` varsayilani `pkl` yapildi |
| 6 | `scipy` eski (`as_quat(scalar_first=)` yok) | 1.15.2'ye yukseltildi |
| 7 | **Turkce "İ" karakteri MuJoCo'yu patlatiyor** | **ASCII yola tasindi** |

### 7. engel — en sinsisi

MuJoCo, yolunda Turkce "İ" olan XML dosyasini **acamiyor**:
```
ValueError: ParseXML: Error opening file
  'C:\Users\Gelir İdaresi\...\g1_mocap_29dof.xml'
```
Dosya var, izin var, goreli yolla aciliyor — ama mutlak yolla acilmiyor.
ASCII yolda test edilince sorunsuz calisti.

**Cozum:** GMR `C:\ufbots_tools\GMR` altina tasindi (ASCII).

## Ilk retarget basarili

```
knee_strike_86_06.npz -> g1_test.pkl

fps        : ()
root_pos   : (119, 3)
root_rot   : (119, 4)     quaternion
dof_pos    : (119, 29)    G1 29 DOF
```

29 motor tanindi, IK config `smplx_to_g1.json` kullanildi.

## Calisma dizinleri

```
C:\ufbots_tools\GMR\              GMR (ASCII yol zorunlu)
C:\ufbots_tools\data\amass_trimmed\   girdi (29 klip)
C:\ufbots_tools\data\g1_retargeted\   cikti
```

Proje klasoru (`Desktop\ufbots`) ana konum olarak kaliyor; sadece
MuJoCo'nun dokundugu dosyalar ASCII yolda.

---

# KESME HATASI DUZELTILDI — 2026-09-23

## Hata

Kullanici "knee strike de diz atmiyor" dedi — hakliydi. Olctum:

```
knee_strike_86_06:
  gercek diz vurusu   -> 54.1s  (109 derece)
  bizim kestigimiz an -> 36.3s
```

83 saniyelik klipte diz vurusunu tamamen kacirmisiz.

**Sebep:** `trim_bvh.py` kesme noktasini GENEL eklem hareketliligine gore
seciyordu. Ama uzun klipte en hareketli an diz vurusu degil (yurume,
donme olabilir). Hareketin TURUNE bakmiyordu.

Kaynak veriyi de kontrol ettim: orada da 22 derece cikti — yani hata
retarget'ta degil, kesmede.

## Cozum: eklem-farkindali kesme

`retrim_smart.py` — her kategori icin dogru eklemi izler:

| Kategori | Izlenen sinyal |
|---|---|
| `knee_strike` | diz acisi |
| `jump_*` | kalca yuksekligi |
| `kick`, `front_kick` | kalca pitch |
| `punch` | dirsek + omuz |
| `spin` | govde |

### Degisen kesme noktalari

```
knee_strike_86_06     36.3s -> 54.1s
jump_kick_86_03       18.5s -> 49.8s
punch_86_05           11.1s -> 39.3s
punch_kick_combo_86   74.6s -> 40.9s
```

### Sonuc (diz aci araligi)

| Klip | ESKI | YENI | Fark |
|---|---|---|---|
| **knee_strike_86_06** | 15° | **120°** | **+106°** |
| jump_kick_90_05 | 81° | 82° | +0° |
| jump_kick_86_03 | 100° | 103° | +4° |
| front_kick_135_04 | 133° | 133° | +0° |
| punch_86_05 | 72° | 33° | -40° (kol odakli kesim) |

**Gorsel dogrulama:** yeni kontak sayfasinda 6. karede diz belirgin
sekilde yukarida. Onceki versiyonda robot sadece ayakta duruyordu.

## Cikti

```
C:\ufbots_tools\data\amass_smart\    29 klip, 110 s  (dogru kesim)
C:\ufbots_tools\data\g1_smart\       29 PKL (G1 retarget)
results/g1_smart/                    video + kontak sayfasi
```

## Kullanicinin sorularina cevap

**"Bu bokator mu?"** — Hayir. Veri CMU mocap'tan: jenerik dovus/akrobasi.
Bokator iki kez arandi, iki kez bulunamadi (BONES-SEED'de sifir sonuc,
Kimodo stil ismini tanimiyor). Elimizde ucan tekme + yumruk + donus var.

**"Modeli biz mi egittik?"** — Hayir, HENUZ HIC EGITIM YAPILMADI.
Su ana kadar sadece veri hazirligi. Kinematik retarget — fizik yok,
denge yok. SONIC fine-tune icin GPU lazim, o asamaya gelinmedi.

**"Uzun hareket / kendisiyle dovusturme?"** — Ikisi de hayir.
Klipler bilerek 4 saniye (uzun klip verirsen robot yurumeyi ogrenir).
Kendisiyle dovusme icin iki robot + fizik etkilesimi + self-play RL
gerekir; SONIC bir motion tracking sistemi, "rakibini yen" demiyor.
