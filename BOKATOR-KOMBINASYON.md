# Bokator Kombinasyonlari — G1 icin

Bokator'un gercek teknik repertuari arastirildi, elimizdeki veriyle
eslestirildi. Amac: **tek hareket degil, bokator mantigini tasiyan
kombinasyonlar**.

---

## 1. Bokator gercekte ne iceriyor

Kaynak: [Wikipedia](https://en.wikipedia.org/wiki/Bokator),
[Fight Encyclopedia](https://fightencyclopedia.com/martial-arts/striking/southeast-asian/bokator)

**10,341 teknik / 341 set** iddia ediliyor. Ana kategoriler:

| Khmer adi | Teknik | G1'de |
|---|---|---|
| **Dum** | Dirsek vurusu (yakin mesafe) | ✅ kol hareketi |
| **Chanleak** | Diz vurusu — **sik sik ucarak** | ⚠️ zor, veri var |
| **Kbach Kchey** | Eklem kilidi | ❌ iki kisi gerekir |
| **Kbach Chhlang** | Supurme ve atis | ❌ iki kisi |
| **Kbach Bantheay** | Bogma | ❌ iki kisi |
| *jruk tajak* | Kalca atisi | ❌ iki kisi |
| *kamlang* | Tek bacak yere indirme | ❌ iki kisi |
| *jruk kbach* | Omuz atisi | ❌ iki kisi |

Ayrica **shin kick** (kaval kemigi tekmesi) ve **kafa vurusu** var.

### Hayvan stilleri (341 stil)

`domrei` fil, `krapeu` timsah, `tor` aslan, `seah` at, `preap` kus,
`neak` ejderha, `sdach swaa` maymun kral, `kdam` yengec, `tiea` ordek.

- **Horse (seah):** ileri yuklenme, kararli durus, guclu tekmeler
- **Crane:** dengeli tekmeler, kacinma
- **Eagle:** pence vuruslari, **havadan teknikler**

> Bu bizim icin onemli: bokator'un kendi icinde **ucan teknik gelenegi**
> var (Chanleak + Eagle stili). Yani ucan diz uydurma degil, ozgun.

---

## 2. Elimizdeki veri — bokator ogelerine eslesme

29 klip olculdu (G1 eklem aciklari, derece):

### CHANLEAK — ucan diz/tekme ✅ GUCLU

| Klip | diz | sicrama | Not |
|---|---|---|---|
| `jump_kick_75_16` | **149** | **1.48** | en iyi |
| `jump_kick_90_05` | 82 | 1.46 | |
| `jump_kick_90_06` | 83 | 1.44 | |
| `jump_kick_90_07` | 82 | 1.44 | |
| `jump_kick_86_03` | 103 | 1.23 | |

Havada faz + yuksek diz acisi — Chanleak'in tam karsiligi.

### Ayakta diz vurusu ✅

`knee_strike_86_06` — diz **120°**, sicrama 1.02 (ayakta).
Kesme duzeltmesinden sonra gercek diz kalkisi goruluyor.

### DUM — dirsek ⚠️ DOLAYLI

En yuksek dirsek aciklari:

| Klip | dirsek |
|---|---|
| `punch_143_23` | **130** |
| `jump_kick_86_01` | 116 |
| `punch_kick_combo_141_14` | 114 |
| `punch_144_21` | 112 |

Ama bunlar **yumruk**, dirsek vurusu degil. Dirsek acisi buyuk cunku
kol bukuluyor — hedefe dirsekle vurmuyor.

**Gercek Dum icin veri YOK.** Uretmek gerekiyor (bkz. bolum 4).

### Govde donusu (atis on hazirligi) ✅

| Klip | govde |
|---|---|
| `spin_88_10` | **163** |
| `jump_kick_90_05` | 136 |
| `jump_kick_90_06` | 133 |

Atisin kendisi yok ama **govde rotasyonu** var — `jruk tajak`
(kalca atisi) hazirlik fazina benziyor.

### GURES / ATIS ❌ YOK

CMU'da arandi: "throw" hepsi top atma, "sweep" temizlik, "grapple"
dolaptan esya alma. **Gercek gures verisi yok.**

---

## 3. Gures icin kaynaklar (arastirildi)

### ReMoCap — ⭐ EN IYI, DOGRUDAN INDIRILEBILIR

```
https://vcai.mpi-inf.mpg.de/projects/remos/ReMocap.zip
1.38 GB — form yok, dogrudan link (test edildi, calisiyor)
```

- 275.7K kare, 2.04 saat
- **Ninjutsu** (25 fps) + Lindy Hop (50 fps)
- Iki kisilik, tam vucut + parmak
- Max Planck Enstitusu

Ninjutsu = atis, kilit, yere indirme — bokator'un gures kismina
en yakin acik veri.

### Digerleri

| Dataset | Icerik | Erisim |
|---|---|---|
| **Hi4D** | 100 dizi, 20 cift, SMPL + temas etiketi | acik |
| **CHI3D** | 631 dizi, SMPL-X | acik |
| **ExPI** | 115 dizi Lindy Hop **havadan figurler** | acik |
| **Harmony4D** | vahsi ortamda **gures** | NeurIPS 2024 |

> ⚠️ Hepsi **iki kisilik**. Tek kisiye ayirmak gerekir — atan kisinin
> hareketi alinir, atilan atilir.

---

## 4. Eksikler icin uretim

Veri bulunamayan ogeler:

| Oge | Yontem |
|---|---|
| **Dum** (dirsek vurusu) | Kendi cekimin + GVHMR, ya da Kimodo tarif istemi |
| Shin kick | Kimodo: "fighter kicks with the shin at close range" |
| Hayvan duruslari | Kimodo: "low crouching stance like a crocodile" |
| Kafa vurusu | Uretmeye degmez, G1'de anlamsiz |

**Kimodo notu:** stil ismini tanimiyor ("bokator" ise yaramiyor) ama
kisa mekanik terimler calisiyor. `spin_named` testi bunu gosterdi
(%117 hareketlilik). Yani "flying knee strike" yaz, "bokator chanleak" yazma.

---

## 5. Onerilen kombinasyonlar

Bokator mantigi: **yakin mesafe + dirsek/diz + denge bozma**.
Elimizdeki parcalarla kurulabilecek diziler:

### A. "Chanleak Combo" — ucan diz serisi ✅ HAZIR
```
dovus durusu -> ileri adim -> UCAN DIZ -> inis -> gard
kaynak: front_kick_135_04 + jump_kick_75_16 + attack_sequence_76_01
```
Tum parcalar elimizde. **En gerceklestirilebilir.**

### B. "Dum-Chanleak" — dirsek + diz ⚠️ DIRSEK EKSIK
```
clinch pozisyonu -> DIRSEK -> DIZ -> geri cekilme
eksik: gercek dirsek vurusu
```

### C. "Seah" (at stili) — ileri yuklenme ✅ HAZIR
```
alcak durus -> ileri patlama -> ardisik tekme -> durus
kaynak: kick_74_04 + punch_kick_combo_141_14
```

### D. "Kbach Chhlang" — atis ❌ VERI YOK
```
kavrama -> govde donusu -> atis
ReMoCap gerekiyor
```

---

## 6. Gercekci oncelik

| Oncelik | Is | Durum |
|---|---|---|
| 1 | **Chanleak (ucan diz) tek hareket** | ✅ veri hazir |
| 2 | Ayakta diz + tekme kombinasyonu | ✅ veri hazir |
| 3 | Dirsek vurusu uret (Kimodo/video) | ⬜ |
| 4 | ReMoCap indir, Ninjutsu'yu incele | ⬜ |
| 5 | Gures/atis (tek kisiye ayirarak) | ⬜ zor |

**Dürüst degerlendirme:** yarismada 1 ve 2 ile guclu bir submission
cikar. 3 makul. 4-5 ayri bir proje buyuklugunde ve G1 yere inip
kalkamadigi icin muhtemelen egitimde tutmaz.

---

## 7. Anlatim onerisi

Bokator'u **birebir kopyalamak** yerine:

> "Bokator'un uc ilkesini G1'e uyarladim: yakin mesafe dirsek/diz
> vuruslari (Dum/Chanleak), hayvan duruslarindan gelen alcak denge
> pozisyonlari, ve govde rotasyonuyla guc uretimi. Gures ve yere
> inme kismini bilerek disarida biraktim cunku G1 yerden kalkamiyor."

Bu hem durust hem ozgun. "Bokator yaptim" demekten daha guclu.

*Motion Data by Bones Studio*
EOF
echo "kaydedildi"
---

# UYGULAMA — 2026-09-23

## Kombinasyonlar kuruldu ✅

`scripts/build_combo.py` — klipleri birlestirip dizi kurar. Gecislerde
8 kare harmanlama, kok pozisyonu hizalama, quaternion normalizasyon.

| Kombinasyon | Sure | diz | sicrama | Durum |
|---|---|---|---|---|
| **chanleak** | 4.6s | **149°** | **1.62** | ✅ dogrulandi |
| dum_chanleak | 4.6s | 119° | 1.47 | ✅ |
| knee_combo | 4.6s | 119° | 1.17 | ✅ |
| seah | 5.1s | 108° | 1.04 | ✅ |

### chanleak gorsel dogrulama

Kontak sayfasi (`results/combos/chanleak_sheet.png`):
```
durus -> comelme -> sicrama -> HAVADA YUKSEK DIZ -> inis -> gard
```
5-6. karede robot tamamen havada, golge yerde ayri. Tam Chanleak yapisi.

**Not:** sicrama 1.62 — tek kliplerin hepsinden yuksek (en iyi tek klip
1.48'di). Kombinasyon giris adimini ekleyince ivme artiyor.

## ReMoCap indirildi ✅

```
1.38 GB — dogrudan link, form yok
C:\ufbots_tools\data\ReMocap.zip
```

### Icerik

| | |
|---|---|
| Ninjutsu BVH | **158 dosya** |
| Sahne (shot) | **79** (her biri 2 kisi: p0, p1) |
| Bolum | train 102, test 56 |
| Format | BVH, 25 fps, **54 eklem** (parmaklar dahil) |

### GURES/YERE INME BULUNDU ✅

Kok yuksekligi / medyan orani — dusuk = yere inme:

| Klip | oran | sure |
|---|---|---|
| `train_shot_033_p1` | **0.13** | 32s |
| `test_shot_024_p1` | **0.13** | 27s |
| `test_shot_020_p0` | 0.14 | 25s |
| `train_shot_085_p0` | 0.14 | 95s |

0.13 = kalca medyanin %13'une dusmus → kisi yerde.

**Bu tam aradigimiz sey:** bokator'un `Kbach Chhlang` (atis) ve
`kamlang` (yere indirme) ogelerinin gercek mocap karsiligi.

### Onemli kisit

Iki kisilik veri. Atis icin:
- **Atan kisi** (p0 veya p1, yuksek kalan) → G1'e ogretilebilir
- **Atilan kisi** (yere inen) → G1 yapamaz, kullanilmaz

Yani her sahneden sadece **bir kisiyi** alacagiz.

## Sonraki adim

1. Ninjutsu sahnelerinde atan/atilan ayrimi yap
2. Atan kisinin hareketini kes (atis anina gore)
3. CMU iskeleti degil — ReMoCap 54 eklem, SMPL fit gerekebilir
4. G1'e retarget et, MuJoCo'da izle

---

# GURES BORU HATTI — 2026-09-24

## Yapildi

| Adim | Sonuc |
|---|---|
| ReMoCap indirme | ✅ 1.38 GB |
| Ninjutsu cikarma | ✅ 158 BVH, 79 sahne |
| Atan/atilan ayrimi | ✅ 79 sahne etiketlendi |
| Temiz atis secimi | ✅ **33 sahne** (atan ayakta, atilan yerde) |
| Atis anina gore kesme | ✅ 20 klip, 80 s |
| Eklem adi donusumu | ✅ 14/14 (ReMoCap -> xsens) |
| G1 retarget | ⚠️ **KISMEN** — asagi bak |

## Rol ayrimi nasil yapildi

Kok yuksekligi / medyan orani:
- **atan**  : >0.60 (ayakta kalir)
- **atilan**: <0.35 (yere iner)

33 sahne temiz cikti. 23 sahne "yer guresi" — ikisi de yerde, kullanilmaz.

Atis ani, ATILAN kisinin en hizli dustugu andan bulundu; ATAN kisinin
hareketi o ana gore kesildi.

## Retarget: GMR scriptleri calismadi

| Script | Sorun |
|---|---|
| `bvh_to_robot.py` | sadece `lafan1`/`nokov` formati |
| `xsens_bvh_to_robot.py` | parser ReMoCap kanal duzenini reddediyor (`IndexError: bvh_rot_idx`) |

**Cozum:** BVH'yi kendimiz okuyup ileri kinematik (FK) ile dunya
koordinatlarini hesaplayip GMR'nin IK cekirdegine besledik
(`scripts/throws_to_g1.py`).

### Yol boyunca duzeltilen hatalar

1. **Birim**: cm degil **mm** (kalca 865 mm)
2. **BVH hiyerarsi ayristirmasi bozuktu** — 5 eklem koksuz kaliyordu.
   `{` / `}` takibi duzeltildi, simdi tek kok (Pelvis)
3. **Kok offset'i** iki kez ekleniyordu
4. **Y-up -> Z-up donusumu**: `-90` yanlisti, dogrusu **`+90`**
   (govde-yukari vektoru [0,0,1] cikmali)

## Kalan sorun: IK karelerin yarisinda cokuyor

| | Kaynak (BVH) | Robot (retarget) |
|---|---|---|
| dik kare orani | **%100** | **%53** |
| kalca yuksekligi | 0.84 m | 0.71 m |

GMR'ye giden hedefler saglikli (kalca 0.84 m, ayaklar 0.09-0.18 m) ama
IK cozucu karelerin yarisinda govde dikligini koruyamiyor.

### Karsilastirma

```
CMU yolu (AMASS SMPL-X -> GMR):   dik %96   ✅ calisiyor
ReMoCap yolu (BVH FK -> GMR):     dik %53   ⚠️ bozuk
```

Fark: CMU yolunda GMR'nin kendi SMPL-X yukleyicisi kullaniliyor
(olcekleme, kalibrasyon dahil). Bizim FK yolumuzda bu katman yok.

## Degerlendirme

Gures verisi **var ve dogru kesildi** ama G1'e temiz aktarilamadi.
Muhtemel cozumler:

1. ReMoCap BVH -> SMPL-X fit -> GMR (CMU yoluyla ayni)
2. GMR'nin `human_scale_table` parametrelerini ReMoCap iskeletine gore ayarla
3. IK sonrasi govde dikligi filtresi (kotu kareleri ele)

**Oncelik degerlendirmesi:** Chanleak/knee_combo kombinasyonlari
calisiyor ve yarisma icin yeterli. Gures hatti ek is gerektiriyor ve
G1 zaten yere inip kalkamadigi icin egitimde tutma ihtimali dusuk.
