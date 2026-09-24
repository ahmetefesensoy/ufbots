# G1 Bokator — Veri Seti Raporu

**32 klip · 126 saniye · 30 fps · Unitree G1 29-DOF**

Kaynak: CMU Mocap → AMASS SMPL-X → GMR retarget → G1


## Kalite sureci

| Asama | Klip |
|---|---|
| CMU katalogunda dovus hareketi | 35 |
| Eklem-farkindali kesme sonrasi | 29 |
| Kombinasyon kurma | +4 |
| Yumusatma + limit kirpma | 33 |
| **Kalite esigini gecen** | **32** |
| Elenen / incelenecek | 1 |

## Hareket ailesi dagilimi

| Aile | Klip | Toplam agirlik |
|---|---|---|
| `jump_kick` | 6 | 10.3 |
| `punch` | 6 | 5.2 |
| `kick` | 5 | 4.9 |
| `kombinasyon` | 4 | 8.6 |
| `attack_sequence` | 3 | 2.8 |
| `front_kick` | 3 | 2.5 |
| `punch_kick_combo` | 2 | 1.9 |
| `knee_strike` | 1 | 2.0 |
| `spin` | 1 | 1.0 |
| `jump_spin_kick` | 1 | 0.4 |

## En yuksek puanli klipler

| Klip | Puan | Diz | Sicrama | Dik% | Agirlik |
|---|---|---|---|---|---|
| `attack_sequence_76_01` | 100 | 47° | 1.07 | 100% | 1.00 |
| `jump_kick_86_03` | 100 | 103° | 1.24 | 100% | 2.00 |
| `kick_74_03` | 100 | 122° | 1.06 | 100% | 1.00 |
| `kick_74_05` | 100 | 98° | 1.03 | 100% | 1.00 |
| `kick_74_06` | 100 | 108° | 1.02 | 100% | 1.00 |
| `knee_strike_86_06` | 100 | 120° | 1.02 | 100% | 2.00 |
| `spin_88_10` | 100 | 65° | 1.05 | 100% | 1.00 |
| `punch_143_23` | 99 | 44° | 1.02 | 100% | 0.99 |
| `kick_74_04` | 99 | 105° | 1.12 | 100% | 0.99 |
| `attack_sequence_76_02` | 98 | 39° | 1.02 | 100% | 0.98 |

## Imza hareketler

Egitimde daha sik orneklenen klipler (agirlik ≥ 1.5):

| Klip | Agirlik | Diz acisi | Sicrama |
|---|---|---|---|
| `chanleak` | **2.65** | 149° | 1.61 |
| `knee_combo` | **2.35** | 119° | 1.17 |
| `jump_kick_86_03` | **2.00** | 103° | 1.24 |
| `knee_strike_86_06` | **2.00** | 120° | 1.02 |
| `seah` | **1.93** | 107° | 1.04 |
| `jump_kick_86_01` | **1.91** | 125° | 1.04 |
| `jump_kick_75_16` | **1.82** | 149° | 1.49 |
| `dum_chanleak` | **1.63** | 118° | 1.47 |
| `jump_kick_90_06` | **1.56** | 83° | 1.46 |
| `jump_kick_90_05` | **1.52** | 82° | 1.49 |

## Olcum tanimlari

- **dik%** — govde-yukari vektorunun z bileseni > 0.8 olan kare orani
- **sicrama** — kalca yuksekligi / medyan (1.0 = hic havalanma yok)
- **jitter** — eklem acisinin ikinci farkinin ortalamasi (titreme)
- **puan** — dik%(40) + jitter(25) + cokme(20) + genlik(15)

## Bilinen sinirlar

- Kaynak veri jenerik dovus mocap'i; **bokator'un kendisi degil**
- Dirsek vurusu (Dum) dolayli — yuksek dirsek acisi yumruktan geliyor
- Gures/atis hatti kismi calisiyor (IK karelerin %53'unde cokuyor)
- Ucan teknikler kinematik olarak dogru, fizik egitiminde tutmayabilir

---

*Motion Data by Bones Studio*