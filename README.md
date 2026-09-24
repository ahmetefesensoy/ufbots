# ufbots — G1 Bokator

Unitree G1'e **Chanleak** (bokator'un ucan diz vurusu) ve yakin mesafe
dovus kombinasyonlari ogretme projesi.

> Bokator'u birebir kopyalamiyoruz. Uc ilkesini G1'e uyarliyoruz:
> yakin mesafe diz/dirsek vuruslari, hayvan duruslarindan gelen alcak
> denge pozisyonlari, govde rotasyonuyla guc uretimi. Gures ve yere
> inme kismi bilerek disarida — G1 yerden kalkamiyor.

*Motion Data by Bones Studio*

---

## Durum

| Asama | Durum |
|---|---|
| Veri kaynagi arastirmasi | ✅ |
| CMU mocap -> AMASS SMPL-X | ✅ 29 klip |
| GMR ile G1 retarget | ✅ 29/29 |
| Bokator kombinasyonlari | ✅ 4 dizi |
| Gures (ReMoCap Ninjutsu) | ⚠️ kismi (bkz. sinirlar) |
| SONIC egitim formati | ✅ 33 hareket, 129 s |
| **Fine-tune** | ⬜ GPU bekliyor |
| ONNX export | ⬜ |

---

## Hareket repertuari

### Kombinasyonlar (`g1_combos`)

| Ad | Sure | Diz acisi | Sicrama | Bokator karsiligi |
|---|---|---|---|---|
| **chanleak** | 4.6s | **149°** | **1.62** | Chanleak (ucan diz) |
| dum_chanleak | 4.6s | 119° | 1.47 | Dum + Chanleak |
| knee_combo | 4.6s | 119° | 1.17 | ayakta diz serisi |
| seah | 5.1s | 108° | 1.04 | Seah (at stili) |

`sicrama` = kalca yuksekligi / medyan. 1.62 = %62 havalanma.

### Tekil hareketler (`g1_smart`)

29 klip: ucan tekme (6), yumruk (6), tekme (5), donus (5),
on tekme (5), diz vurusu, saldiri dizisi.

---

## Boru hatti

```
CMU mocap katalogu
  -> dovus hareketi secimi (35/239)
  -> AMASS SMPL-X karsiliklari
  -> eklem-farkindali kesme (vurus anina gore)
  -> GMR retarget -> G1 29 DOF
  -> kombinasyon kurma
  -> SONIC egitim formati
```

### Kritik detaylar

**Eklem-farkindali kesme.** Genel hareketlilige gore kesmek yanlis
sonuc veriyordu: 83 saniyelik klipte diz vurusu 54.1s'de ama genel
hareket tepesi 36.3s'deydi. Her kategori icin dogru eklem izleniyor:

| Kategori | Izlenen |
|---|---|
| `knee_strike` | diz acisi |
| `jump_*` | kalca yuksekligi |
| `kick` | kalca pitch |
| `punch` | dirsek + omuz |

Duzeltme sonrasi `knee_strike` diz araligi **15° -> 120°**.

**Dosya adlari.** NVIDIA'nin filtresi sadece dosya adina bakiyor
(`cartwheel`, `handstand`, `box_jump`...). Adlarimiz temiz tutuldu,
hicbiri elenmiyor.

---

## Kurulum

### Yerel (veri hazirligi)

```bash
pip install -U huggingface_hub pandas pyarrow mujoco imageio imageio-ffmpeg
```

Windows'ta Turkce kullanici adi varsa: MuJoCo, yolunda "İ" olan XML'i
acamiyor. Araclar `C:\ufbots_tools\` altina kurulur (ASCII yol).

### GPU makinesi (egitim)

```bash
bash scripts/setup_nebius.sh      # GR00T-WBC + checkpoint
# Isaac Lab v2.3.2 ayrica kurulmali
```

---

## Kullanim

```bash
# 1. Veri (yerel)
python scripts/fetch_cmu.py                  # CMU BVH indir
python scripts/select_combat.py              # dovus hareketlerini ayikla
python scripts/retrim_smart.py               # eklem-farkindali kesme
python scripts/retarget_headless.py          # G1'e retarget
python scripts/build_combo.py                # kombinasyonlari kur
python scripts/export_for_sonic.py           # egitim formatina cevir

# 2. Onizleme
python scripts/preview_g1_pkl.py --dir C:/ufbots_tools/data/g1_combos
python scripts/preview_g1_pkl.py --pkl <x.pkl> --video out.mp4
python scripts/contact_sheet.py out.mp4

# 3. Egitim (GPU makinesi)
bash scripts/train_sonic.sh convert
bash scripts/train_sonic.sh replay           # gozle dogrula
bash scripts/train_sonic.sh train
bash scripts/train_sonic.sh eval   <ckpt>
bash scripts/train_sonic.sh export <ckpt>    # ONNX
```

---

## Scriptler

| Script | Is |
|---|---|
| `fetch_cmu.py` | CMU mocap BVH indirici |
| `select_combat.py` | dovus hareketi secimi + temiz adlandirma |
| `analyze_bvh.py` | BVH metrikleri, G1 uygunluk puani |
| `retrim_smart.py` | eklem-farkindali kesme |
| `extract_amass.py` | AMASS arsivinden secici cikarma |
| `retarget_headless.py` | SMPL-X -> G1 (pencere acmadan) |
| `build_combo.py` | kombinasyon kurma (harmanli gecis) |
| `export_for_sonic.py` | SONIC egitim formati (CSV + motion_lib) |
| `preview_g1_pkl.py` | MuJoCo onizleme + metrik |
| `contact_sheet.py` | videodan kontak sayfasi |
| `train_sonic.sh` | fine-tune hatti |
| `throws_to_g1.py` | ReMoCap gures retarget (kismi) |

---

## Sinirlar — durust degerlendirme

**Gures/atis kismi calismiyor.** ReMoCap Ninjutsu verisi indirildi,
33 temiz atis ayiklandi, ama G1'e retarget'ta IK karelerin %53'unde
govde dikligini koruyamiyor (kaynak %100 dik). Ek is gerekiyor.

**Dirsek vurusu (Dum) dolayli.** Elimizdeki yuksek dirsek acilari
yumruktan geliyor, hedefe dirsekle vurmuyor. Gercek Dum verisi yok.

**Ucan teknikler egitimde tutmayabilir.** Veri saglikli (sicrama 1.62,
havada faz gercek) ama G1'in havada faz + inis darbesini ogrenmesi zor.
Denemeye deger, garanti yok.

**Bokator degil, bokator-esinli.** Kaynak veri CMU mocap — jenerik
dovus/akrobasi. Bokator'un kendisi hicbir acik datasette yok
(BONES-SEED: 0 sonuc; Kimodo stil ismini tanimiyor).

---

## Kaynaklar

- [CMU Mocap](http://mocap.cs.cmu.edu/) — ucretsiz, kisitlamasiz
- [AMASS](https://amass.is.tue.mpg.de/) — CMU'nun SMPL-X karsiligi
- [SMPL-X](https://smpl-x.is.tue.mpg.de/) — vucut modeli
- [GMR](https://github.com/YanjieZe/GMR) — SMPL-X -> humanoid retarget
- [GR00T-WBC / SONIC](https://github.com/NVlabs/GR00T-WholeBodyControl)
- [BONES-SEED](https://huggingface.co/datasets/bones-studio/seed)
- [ReMoCap](https://vcai.mpi-inf.mpg.de/projects/remos/) — Ninjutsu
