# ufbots — Kazandiracak Unsurlar

Form 7 alan istiyor: track, proje adi, writeup, GitHub, ONNX policy,
dataset, sim video. Bunlarin hepsi **giris bileti** — herkes dolduracak.
Fark yaratacak seyler asagida.

---

## 1. En buyuk kaldirac: BASARISIZLIGI OLCMEK

Cogu katilimci "calisti" videosu atacak. Biz **nicel kanit** sunabiliriz.

Elimizde zaten var:
- Her klip icin 0-100 kalite puani (dik%, jitter, cokme, genlik)
- Egitim oncesi/sonrasi metrik karsilastirmasi
- Neyin tutmadigi ve **neden** tutmadigi

> "Ucan dizi denedim, kinematik olarak dogru aktardim (sicrama 1.62,
> diz 149 derece) ama fizik egitiminde inis darbesi yuzunden %X basari
> aldim" — bu, "kick calisti" demekten cok daha guclu.

**Yapilacak:** egitim sonrasi `success_rate`, `mpjpe_l`, `mpjpe_g`
degerlerini klip bazinda tablolastir.

---

## 2. Boru hattinin kendisi bir katki

Yasadigimiz ve cozdugumuz sorunlar baskalarinin da basina gelecek:

| Sorun | Cozumumuz |
|---|---|
| GMR BVH scriptleri ReMoCap'i kabul etmiyor | kendi FK + GMR IK |
| Turkce yol MuJoCo'yu patlatiyor | ASCII yol zorunlulugu |
| `chumpy` Python 3.12'de calismiyor | kaynak yamasi |
| `proxsuite` Windows'ta derlenmiyor | qpsolvers alternatifi |
| Genel hareketlilige gore kesme yanlis | **eklem-farkindali kesme** |

**Eklem-farkindali kesme** gercek bir katki: 83 saniyelik klipte diz
vurusu 54.1s'de, genel hareket tepesi 36.3s'de. Yanlis kesince diz
araligi 15 derece, dogru kesince 120 derece.

**Yapilacak:** README'de "Windows/Turkce kurulum tuzaklari" bolumu.
Bu, jurinin repo'yu klonlayip calistirabilmesi demek.

---

## 3. Veri seti olarak deger

Form ayri bir "Dataset — Hugging Face" alani istiyor. Cogu kisi
kullandigi veriyi yukleyecek. Biz **islenmis + puanlanmis** set verebiliriz:

```
32 klip · 126 s · G1 29-DOF
  + kalite puani (0-100)
  + egitim agirligi
  + kategori etiketi (chanleak/dum/seah)
  + bilinen sinirlar
```

Baskasinin dogrudan kullanabilecegi sey. HF dataset karti + manifest.json.

**Yapilacak:** `scripts/export_hf_dataset.py` — HF'ye yuklenebilir paket.

---

## 4. Anlatim: "kopyalama" degil "uyarlama"

Bokator'u birebir yapamiyoruz (veri yok, G1 yere inemiyor).
Bunu zayiflik degil **tasarim karari** olarak sunmak:

> Bokator'un 10,341 teknigi var ama G1'in 29 eklemi ve yerden
> kalkamama kisiti var. Uc ilkeyi sectim:
> 1. **Chanleak** — ucan diz (bokator'un imza teknigi, Eagle stili)
> 2. **Seah** — at stili ileri yuklenme (alcak denge)
> 3. **Govde rotasyonu** — guc uretimi
>
> Gures/yere inme kismini bilerek disarida biraktim: G1 yerden
> kalkamiyor, o veriyi egitime koymak robotu duserken birakmak demek.

Bu, jurinin "neden bokator'un yarisini yapmadin" sorusuna hazir cevap.

---

## 5. Teknik ozgunluk: agirlikli ornekleme

SONIC fine-tune'da klipleri esit orneklemek yerine kalite x imza
agirligi kullaniyoruz:

```
chanleak         2.65
knee_combo       2.35
jump_kick_*      1.5-2.0
siradan yumruk   0.74
```

Sebep: 32 klip esit orneklenirse 6 ucan tekme kaybolur.
**Bu, writeup'ta anlatilacak somut bir metodoloji.**

---

## 6. Yapilabilecek ek isler (etki sirasiyla)

### A. Egitim + olcum ⭐⭐⭐  [GPU gerekli]
En buyuk eksik. Onsuz "veri hazirladim" demis oluyoruz.
`success_rate > 0.97` hedefi, klip bazli tablo.

### B. Sim2real notu ⭐⭐
Gercek G1 yok ama **MuJoCo'da fizikli dogrulama** yapilabilir:
kinematik replay yerine gercek fizik altinda politika kosturmak.
Arastirma da bunu soyluyor: sim2sim dogrulamasi gecen politikalar
gercek robota degisiklik olmadan aktariliyor.

### C. Interaktif demo ⭐⭐
HF Space: metin -> hareket secimi -> MuJoCo render.
Juri tarayicidan deneyebilir. Kimodo zaten Gradio kullaniyor.

### D. Kombinasyon uretici ⭐
Su an 4 sabit kombinasyon var. Kullanici "dirsek + diz + geri cekil"
yazinca otomatik dizi kuran arayuz.

### E. Karsilastirma tablosu ⭐
Ayni hareketi 3 yolla uretip karsilastir:
BONES-SEED hazir vs CMU retarget vs Kimodo uretimi.
Hangisinin G1'de daha iyi tuttugunu olc.

---

## 7. Onceliklendirme

| Is | Etki | Maliyet | GPU? |
|---|---|---|---|
| **HF dataset paketi** | yuksek | dusuk | hayir |
| **Windows kurulum rehberi** | orta | dusuk | hayir |
| **Fizikli MuJoCo dogrulama** | yuksek | orta | hayir |
| Egitim + metrik tablosu | **cok yuksek** | yuksek | **evet** |
| HF Space demo | orta | orta | hayir |
| Kombinasyon uretici | dusuk | orta | hayir |

**Simdi yapilabilecekler (GPU'suz):** HF paketi, kurulum rehberi,
fizikli dogrulama.

---

*Motion Data by Bones Studio*
