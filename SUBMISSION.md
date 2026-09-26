# ufbots — Submission Form İçeriği

Forma kopyalanacak metinler. Track: **Martial Arts**

---

## Project name

```
G1 Chanleak — Bokator Flying Knee
```

Alternatifler:
- `G1 Chanleak Combo`
- `G1 Bokator: Flying Knee Strike`

---

## Writeup

```
G1 CHANLEAK — BOKATOR'S FLYING KNEE

WHAT I TAUGHT

Chanleak, the flying knee strike from Bokator — the Khmer battlefield
martial art recognised by UNESCO. Rather than copying one isolated move,
I built a four-step combination: fighting stance → forward step → airborne
knee strike → landing → guard. 4.6 seconds, 149° of knee flexion, hip
rising to 1.61× its median height.

WHY IT'S HARD

Three reasons, in increasing difficulty.

First, the data does not exist. I searched every open motion dataset for
Bokator: BONES-SEED returns zero matches for "bokator", "khmer", "muay
thai", "capoeira" or "silat". I then tested whether NVIDIA's Kimodo could
generate it from text. It cannot — I measured the distance between
"a bokator fighter performs a khmer elbow strike" and a purely mechanical
description of the same motion: 0.96× the noise floor between two random
samples of the *same* prompt. The model does not recognise the style name.

Second, trimming on the wrong signal destroys the move. My first pass cut
clips at the peak of overall joint motion. In an 83-second CMU clip the
real knee strike happens at 54.1 s, but peak overall motion is at 36.3 s.
Cutting at the wrong moment dropped the knee range from 120° to 15° — the
strike simply was not in the clip. I rewrote the trimmer to track the
joint that defines each category: knee angle for knee strikes, hip height
for airborne techniques, hip pitch for kicks, elbow and shoulder for punches.

Third, and most fundamental: kinematic correctness is not balance. After
retargeting I ran every clip through full MuJoCo physics with a position
controller. Joint tracking error was 2-4° — essentially perfect. Yet all
32 clips fell within 0.7 seconds. I ran a controlled test to locate the
cause: holding the G1's own keyframe pose, the robot stays upright
indefinitely (hip z: 0.790 → 0.792 m). Holding a motion-capture pose, it
collapses (0.699 → 0.128 m). The data was not wrong. Mocap poses are
simply not the robot's equilibrium, and a tracking policy has to learn
that difference.

HOW I DID IT

Pipeline: CMU Mocap → AMASS SMPL-X → GMR retarget → G1 29-DOF → SONIC
fine-tune.

I scanned the CMU catalogue for combat motions (35 of 239 trials), pulled
their AMASS SMPL-X equivalents, trimmed each on its defining joint,
retargeted to the G1 through GMR, then smoothed with a Savitzky-Golay
filter — chosen because it preserves strike peaks while removing IK
jitter. It cut jitter by 35% with zero loss of amplitude: knee angle
stayed at 149°, hop at 1.61.

Every clip was scored 0-100 on upright percentage, jitter, collapse and
amplitude. 32 of 33 passed; the one rejection was an acrobatic backflip
misfiled as a spin kick — something the G1 cannot do. Signature moves
carry higher sampling weight (chanleak 2.65, ordinary punch 0.74) because
uniform sampling would bury six flying kicks among twenty-six ordinary
clips. I mixed in 28 BONES-SEED locomotion clips to prevent catastrophic
forgetting; fine-tuning on strikes alone teaches a robot to forget how
to walk.

Trained from the sonic_release checkpoint for 6,933 iterations on a single
NVIDIA L4 (~10 GPU-hours, roughly $11 of cloud credit).

RESULTS

                    PD control      After training
  Success rate           0%              61%
  mpjpe_g                 —           189.1 mm   (target <200) ✓
  mpjpe_l                 —            38.9 mm   (target <30)
  Progress rate           —              77%

The zero-to-61% shift is the measurement I care about. It is not a
demo — it is the difference between a kinematically valid trajectory and
a policy that can hold balance while executing it.

WHAT I DID NOT SOLVE

mpjpe_l sits at 38.9 mm against a 30 mm target. NVIDIA's own guidance
suggests ~100K iterations for convergence; I ran 6.9K, about 7%. The gap
is compute, not method.

Bokator's grappling — Kbach Chhlang throws, kamlang takedowns — is
deliberately excluded. I processed ReMoCap's Ninjutsu set (79 scenes, 33
clean throws where the thrower stays upright) and built the retarget path,
but the IK holds torso uprightness in only 53% of frames against 100% in
the source. Beyond that, the G1 cannot stand back up from the floor, so
training on ground techniques would teach it to fall and stay down.

The source motions are generic combat mocap, not authentic Bokator
footage. I adapted three principles — close-range knee and elbow strikes,
the low balance of the animal stances, power generation through torso
rotation — rather than claiming to reproduce a 10,341-technique system on
a 29-joint robot.

Motion Data by Bones Studio
```

---

## GitHub repo

```
github.com/<kullanici>/ufbots
```

⬜ Repo henüz push edilmedi — yapılacak

---

## ONNX policy — Hugging Face

```
hf.co/<kullanici>/ufbots-chanleak-g1
```

⬜ Yüklenecek dosya: `model_step_005000_g1.onnx` (58 MB)

---

## Dataset — Hugging Face

```
hf.co/datasets/<kullanici>/ufbots-bokator-g1
```

⬜ Hazır paket: `dist/ufbots-bokator-g1/` (32 klip, CSV+NPZ+manifest)

---

## Sim video — YouTube

```
youtube.com/watch?v=...
```

⬜ Yapılacak: before/after kurgusu
- **Before:** PD kontrol, robot düşüyor (`results/` altındaki kayıtlar)
- **After:** eğitilmiş politika (`videolar.tgz` içindeki 8 video)
- Açıklamaya **"Motion Data by Bones Studio"** yaz
