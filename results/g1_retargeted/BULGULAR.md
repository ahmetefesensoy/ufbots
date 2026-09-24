# G1 Retarget Sonuclari — 2026-09-23

29 CMU klibi SMPL-X uzerinden Unitree G1'e (29 DOF) retarget edildi.

## Ozet

| Metrik | Deger |
|---|---|
| Klip | 29/29 basarili |
| Toplam sure | 119 s |
| Format | root_pos(N,3) + root_rot(N,4) + dof_pos(N,29) |

`sicrama` = kalca yuksekligi / medyan. 1.00 = hic sicrama yok.

## Ucan teknikler CALISTI

| Klip | sicrama | z_max | Gorsel dogrulama |
|---|---|---|---|
| `jump_kick_90_05` | **1.47** | 1.16 m | ✅ robot tamamen havada, golge ayri |
| `jump_kick_75_16` | **1.46** | 1.18 m | ✅ |
| `jump_kick_90_06` | 1.44 | 1.16 m | ✅ |
| `jump_kick_90_07` | 1.44 | 1.16 m | ✅ |
| `jump_kick_86_01` | 1.40 | 1.03 m | ✅ |
| `jump_kick_86_03` | 1.38 | 1.01 m | ✅ |

**Onemli:** havada faz retarget'ta KORUNDU. Insan mocap'indaki sicrama
G1 eklem acilarina aktarilirken kaybolmadi.

`jump_kick_90_05` kontak sayfasi: 3. karede robot tamamen havada,
5. karede tek ayak ustunde yuksek tekme.

## Sorunlu

| Klip | Durum |
|---|---|
| `jump_spin_kick_88_06` | **Akrobatik takla** — robot bas asagi donuyor. Gorsel carpici ama G1 fizikte yapamaz. |
| `knee_strike_86_06` | sicrama 1.02 — **diz kalkisi kaybolmus**, robot ayakta duruyor |
| `punch_144_21` | z_ort 0.51 m — cok alcak, muhtemelen comelme |

## Kategori dagilimi (sicrama'ya gore)

```
1.35+   ucan teknikler (7 klip)   — havada faz var
1.05-1.35  orta (5 klip)           — hafif sicrama
1.00-1.05  ayakta (17 klip)        — sicrama yok
```

## Sonraki adim

- Egitimde ucan teknikleri ayri agirlikla kullan
- `jump_spin_kick_88_06` gibi akrobatik olanlari ele (G1 yapamaz)
- `knee_strike` icin daha iyi kaynak bul (mevcut klipte diz gorunmuyor)
