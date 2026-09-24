# Kimodo Nis Dovus Sanati Denemesi — Sonuclar

**Tarih:** 2026-09-22
**Model:** nvidia/Kimodo-G1-RP-v1 (700 saat Rigplay mocap, G1'e retarget)
**Uretim:** Kaggle T4, 8 istem x 3 ornek = 24 motion, 5 sn @ 30fps

## Asil soru

Kimodo bokator gibi nis dovus sanatlarini biliyor mu?

Her hareket iki bicimde soruldu:
- `*_named` : stil ismiyle ("a bokator fighter performs a khmer elbow strike")
- `*_desc`  : mekanik tarifle ("steps forward and delivers a downward elbow strike")

## Sayisal sonuc: HAYIR

Ayni istemin kendi 3 ornegi arasindaki fark = **14.3 derece** (taban gurultu).
Isimle vs tarifle farki:

| Karsilastirma | Fark | Tabanin kati | Yorum |
|---|---|---|---|
| bokator_named vs bokator_desc | 13.7° | 0.96x | AYNI |
| muaythai_named vs muaythai_desc | 13.9° | 0.97x | AYNI |
| spin_named vs spin_desc | 15.4° | 1.07x | AYNI |

Uc stilde de fark, rastgele varyasyondan buyuk degil.
**Model stil isimlerini tanimiyor.**

## Hareketlilik (kontrol = %100)

| Istem | Hareketlilik | Bacak aralik | Gozlem |
|---|---|---|---|
| spin_named | **117%** | **143°** | Gercek tekme var (diz yukari, tek ayak denge) |
| muaythai_named | 92% | 111° | Bacak yana savruluyor, roundhouse basligici |
| control_boxing | 100% | 67° | Gard + duz yumruk — saglikli |
| bokator_knee | 66% | 59° | Derin comelme, diz vurusu yok |
| bokator_named | 50% | 64° | Neredeyse hareketsiz |
| spin_desc | 46% | 81° | Zayif |
| bokator_desc | 23% | 54° | Hafif one egilme |
| muaythai_desc | 16% | 57° | En durgun |

## Kritik bulgu: isim > tarif

Beklentinin **tersi** cikti. Mekanik tarif daha iyi calisir sanmistik ama:

- `spin_named` (117%) >> `spin_desc` (46%)
- `muaythai_named` (92%) >> `muaythai_desc` (16%)

Model uzun mekanik tarifleri ("pivots on the left foot and swings the right
leg horizontally at head height") iyi isleyemiyor — muhtemelen egitim
verisindeki aciklamalar kisa ve dogal dilde.

Kisa, yaygin terimler ("spinning back kick", "roundhouse kick") ise
calisiyor cunku bunlar egitim verisinde gecen ifadeler.

## Sonuc

1. **Bokator uretilemez** — model bu stili bilmiyor, hicbir istem bicimi
   ise yaramadi. En iyi bokator ciktisi bile kontrolun %66'si ve dirsek/diz
   vurusu icermiyor.

2. **Spinning back kick UMIT VAR** — `spin_named` kontrolden hareketli,
   ilk saniyede gercek bir tekme var (143° bacak araligi). Tek sorun:
   hareketin geri kalani durgun.

3. **Istem stratejisi:** kisa ve yaygin terim kullan, uzun mekanik tarif yazma.

## Oneri

Bokator'u birak. `spin_named` uzerine git:
- Daha fazla ornek uret (num_samples 10+), en iyisini sec
- Sureyi kisalt (3 sn) — tekme ilk saniyede oluyor, gerisi bos
- Benzer kisa terimler dene: "spinning heel kick", "tornado kick",
  "jumping spinning kick", "capoeira kick"
