# Bokator Dataseti Nasil Cikarilir

Kimodo bokator'u bilmiyor (bkz. [results/kimodo/BULGULAR.md](results/kimodo/BULGULAR.md)).
Hazir veri de yok. Yani veriyi **kendimiz uretmemiz** gerekiyor.

Bu belge dort yolu gercekcilik sirasina gore karsilastirir.

---

## Hedef format (her yol buraya varmali)

```
video/mocap  →  SMPL veya SOMA BVH  →  G1 CSV (29 DOF)  →  motion_lib PKL  →  SONIC fine-tune
```

NVIDIA'nin kendi dokumanindan (`new_embodiments.html`) onerdigi iki retarget araci:

| Arac | Girdi | Cikti | Not |
|---|---|---|---|
| [NVIDIA/soma-retargeter](https://github.com/NVIDIA/soma-retargeter) | **SOMA BVH** | G1 CSV (29 DOF) | NVIDIA'nin onerisi; GPU ister |
| [GMR](https://github.com/YanjieZe/GMR) (ICRA 2026) | **SMPL-X** | herhangi URDF | CPU'da gercek zamanli, daha esnek |

> ⚠️ **Onemli kisit:** soma-retargeter dokumantasyonu acikca soyluyor —
> *"The retargeter currently expects the source hierarchy and naming used by
> the SOMA base skeleton."* Yani YouTube'dan cikardigin rastgele BVH'yi
> kabul etmez. Video yolundan gidersen **GMR** kullanmalisin (SMPL-X alir).

---

## Yol 1 — Video'dan motion cikarma (EN GERCEKCI)

Bokator'un YouTube'da egitim/gosteri videolari var. Tek kameradan 3D poz
cikarma artik olgun bir teknoloji.

### Zincir

```
YouTube videosu
  → GVHMR (video → SMPL)          https://github.com/zju3dv/GVHMR
  → GMR   (SMPL-X → G1 CSV)       https://github.com/YanjieZe/GMR
  → convert_soma_csv_to_motion_lib.py
  → SONIC fine-tune
```

### Neden GVHMR
- SIGGRAPH Asia 2024 / TPAMI 2026 — guncel ve saglam
- **World-grounded**: kamera hareketini insan hareketinden ayirir
  (elde cekilmis videolar icin sart)
- ComfyUI sarmalayicilari var, kurulumu kolaylasmis

### Adimlar
1. 5-10 bokator videosu sec (sabit kamera, tam vucut gorunur, tek kisi)
2. Hareketleri kes: her klip **tek teknik**, 3-6 saniye
3. GVHMR ile SMPL parametrelerini cikar
4. GMR ile G1'e retarget et
5. `preview_mujoco.py` ile gozle dogrula → kotuleri ele
6. PKL'e cevir, fine-tune et

### Gercekci beklenti
| Konu | Durum |
|---|---|
| Kalite | Mocap'tan dusuk; el/ayak detayi kaybolur |
| Hiz | Video basina birkac dakika (GPU ile) |
| Maliyet | Sifir (Kaggle/Colab yeter) |
| Risk | Bulanik/hizli sahnelerde poz kayar |
| **Telif** | ⚠️ **Asagiya bak** |

### Telif uyarisi
YouTube videosundan cikarilan motion verisi turev eser sayilabilir.
Yarisma submission'inda:
- Videolarin kaynagini **acikca belirt**
- Mumkunse Creative Commons lisansli video sec
- Veya kendi cektigin videoyu kullan (bkz. Yol 2)

---

## Yol 2 — Kendi videonu cek (EN TEMIZ)

Telif sorunu yok, kalite kontrolu sende.

### Nasil
1. Bokator teknigi bilen biri bul (veya temel hareketleri kendin yap)
2. Telefonla cek: **sabit tripod**, iyi isik, tam vucut kadrajda, duz zemin
3. Her teknigi 3-5 tekrar, farkli acilardan
4. Yol 1'deki ayni zinciri kullan (GVHMR → GMR)

### Avantaj
- Telif temiz, submission'da sorun cikmaz
- Istedigin tekniği istedigin acidan cekebilirsin
- "Kendi verimi urettim" hikayesi jüri icin guclu

### Dezavantaj
- Bokator bilen birini bulmak gerekiyor
- Yanlis yapilan teknik = yanlis veri

---

## Yol 3 — Mevcut hareketleri birlestirme (HIZLI, DUSUK KALITE)

BONES-SEED'de bokator yok ama **parcalari** var:

| Bokator ogesi | SEED'de en yakin |
|---|---|
| Dirsek vurusu | `shadow_boxing` (yumruk mekanigi) |
| Diz vurusu | `jog_high_knees` (diz kaldirma) |
| Comelme/duruslar | `squat`, `forward_lunge` |
| Donus | `turn_jump`, `ib_combat_turn_jog` |

Bunlari kesip birlestirerek "bokator benzeri" bir dizi olusturulabilir.

**Ama:** bu gercek bokator olmaz, jüri fark eder. Sadece **taban karisimi**
olarak (catastrophic forgetting'i onlemek icin) kullanilmali, asil hareket
olarak degil.

---

## Yol 4 — Elle animasyon (SON CARE)

Blender'da elle keyframe → BVH export → retarget.

Zaman alir, animasyon bilgisi ister, sonuc genelde yapay durur.
Sadece tek bir imza hareketi icin dusunulebilir.

---

## Onerilen plan

```
1. Kendi cektigin 3-5 temel bokator teknigi   (Yol 2, telif temiz)
   + YouTube'dan 5-10 klip                    (Yol 1, cesitlilik)
   ------------------------------------------------
   ~15-30 motion klip

2. Taban karisimi: BONES-SEED'den yurume/duruş/denge hareketleri
   (fine-tune'da robotun yurumeyi unutmamasi icin — SART)

3. GVHMR → GMR → PKL → sonic_release'den fine-tune
```

### Ne kadar veri yeter?

SONIC makalesinde net bir "minimum" yok ama bir referans var: bir gorev icin
**300 teleop trajektorisi** ile %95 basari elde edilmis.

Bizim durumumuz daha dar (tek hareket ailesi), o yuzden:
- **Minimum:** 10-20 temiz klip (tek teknik, cok tekrar)
- **Rahat:** 50+ klip
- **Kritik:** cesitlilik > miktar. Ayni tekmenin 50 kopyasi yerine,
  5 teknigin 10'ar varyasyonu daha iyi genellestirir.

---

## Risk: G1 bokator'u yapabilir mi?

Dürüst olmak gerekirse **hepsini yapamaz**:

| Teknik | G1'de |
|---|---|
| Dirsek vurusu (Dum) | ✅ Kol hareketi, sorun yok |
| Ayakta diz vurusu | ⚠️ Denge zor ama mumkun |
| Ucan diz | ❌ Havada faz — NVIDIA filtresi eler |
| Yere inme / guresme | ❌ Filtre eler |
| Hayvan duruslari (kaplan, timsah) | ⚠️ Derin comelme, DOF limiti |

NVIDIA'nin `filter_and_copy_bones_data.py` scripti zaten "akrobasi, yere
inme, yuksek yuzey" iceren hareketleri eliyor (~%8.7).

**Sonuc:** bokator'un **ayakta yapilan vurus repertuari** (dirsek, diz,
duruslar) gercekci. Akrobatik/yer kismi degil.

---

## Ilk adim

En dusuk riskli baslangic: **tek bir teknik** sec (dirsek vurusu — G1'de
kesin calisir), 10-15 klip topla, tum zinciri uctan uca calistir.

Zincir calistigi dogrulaninca digerlerini ekle.

---

## Kaynaklar

- [GVHMR](https://github.com/zju3dv/GVHMR) — video → SMPL
- [GMR](https://github.com/YanjieZe/GMR) — SMPL-X → G1 (CPU, gercek zamanli)
- [NVIDIA/soma-retargeter](https://github.com/NVIDIA/soma-retargeter) — SOMA BVH → G1
- [SOMA-X](https://github.com/NVlabs/SOMA-X) — parametrik vucut modeli
- [Yeni embodiment kilavuzu](https://nvlabs.github.io/GR00T-WholeBodyControl/user_guide/new_embodiments.html)
- Bokator videolari: [Cambodian Ancient Martial Art (2019)](https://www.youtube.com/watch?v=qzHBZpm6SRE),
  [Khmer Bokator](https://www.youtube.com/watch?v=3FjkU8eaM2E)

*Motion Data by Bones Studio*
