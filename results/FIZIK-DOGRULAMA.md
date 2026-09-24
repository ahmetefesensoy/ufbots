# Fizik Dogrulamasi — Kritik Bulgu

**Tarih:** 2026-09-24
**Yontem:** MuJoCo tam fizik (yercekimi + temas), G1 pozisyon aktuatoru

---

## Sonuc: 32/32 klip dusuyor

| Klip | Takip hatasi | Dusme |
|---|---|---|
| `chanleak` | **3.8°** | 0.7 s |
| `jump_kick_75_16` | 3.0° | 0.9 s |
| `front_kick_144_09` | 1.9° | 0.4 s |
| `attack_sequence_76_01` | 2.9° | 0.7 s |

**Takip hatasi cok dusuk (2-4 derece)** — yani eklem acilari dogru
uygulaniyor. Sorun takipte degil, **dengede**.

## Kok neden: baslangic pozu dengesiz

Kontrollu deney:

```
1. Klip pozunu ver, HIC HAREKET ETTIRME
   -> z: 0.699 -> 0.128   DUSUYOR

2. G1'in kendi keyframe pozunu ver, HIC HAREKET ETTIRME
   -> z: 0.790 -> 0.792   AYAKTA
```

Simulasyon dogru calisiyor. Mocap'ten gelen pozlar G1'in kendi denge
noktasi degil — insan mocap'i robotun kutle dagilimini bilmiyor.

## Bu neden BEKLENEN bir sonuc

Motion tracking politikalarinin var olma sebebi tam olarak bu:

- **Kinematik retarget**: "eklem acilari sunlar olsun" der, dengeyi dusunmez
- **SONIC/RL politikasi**: hedefi takip ederken **dengeyi kendi ogrenir**

PD kontrolcu sadece "acilari kopyala" yapiyor, dusmemek icin ayak
basincini, govde egimini, adim zamanlamasini ayarlamiyor.

## Ne anlama geliyor

| | |
|---|---|
| Veri hatasi mi? | **Hayir** — takip hatasi 2-4° |
| Retarget hatasi mi? | **Hayir** — G1 kendi pozunda ayakta |
| Egitim gerekli mi? | **Evet** — denge ogrenilmeli |

Bu olcum, **SONIC fine-tune'un neden zorunlu oldugunun kaniti**.
"Veriyi hazirladik, calistirdik, olmadi" degil; "kinematik olarak
dogru ama fiziksel denge ogrenilmeli" diyebiliyoruz.

## Egitim sonrasi beklenen

SONIC dokumantasyonundan hedef metrikler:

| Metrik | Hedef |
|---|---|
| `success_rate` | > 0.97 |
| `mpjpe_l` | < 30 mm |
| `mpjpe_g` | < 200 mm |

Bizim PD taban cizgimiz: **%0 basari**. Egitim sonrasi bu sayinin
ne kadar yukseldigi, calismanin gercek olcusu olacak.

## Writeup icin

> Hareketleri G1'e aktardiktan sonra fizik altinda test ettim:
> eklem takip hatasi 2-4 derece (cok iyi) ama 32/32 klip dusuyor.
> Kontrollu deneyle kanitladim ki sorun veride degil — G1 kendi
> keyframe pozunda ayakta kaliyor, mocap pozunda kalmiyor.
> Bu, motion tracking politikasinin neden gerekli oldugunun olcusu:
> kinematik dogruluk denge demek degil.

---

*Motion Data by Bones Studio*
