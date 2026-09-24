"""ReMoCap Ninjutsu atislarini Unitree G1'e retarget eder.

ReMoCap iskeleti Xsens/MotionBuilder standardinda (54 eklem, parmaklar
dahil). GMR'nin `xsens_mvn_to_g1` config'i tam bu yapi icin ama eklem
ADLARI farkli:

    GMR bekliyor        ReMoCap'te
    ------------        ----------
    Pelvis          <-  Hips
    Chest           <-  Spine2
    Left_UpperLeg   <-  LeftUpLeg
    Left_LowerLeg   <-  LeftLeg
    Left_Foot       <-  LeftFoot
    Left_UpperArm   <-  LeftArm
    Left_Forearm    <-  LeftForeArm
    Left_Hand       <-  LeftHand

Bu script BVH'yi okuyup GMR'nin bekledigi adlarla yeniden yazar,
sonra retarget eder.

Kullanim:
    python scripts/remocap_to_g1.py --rename-only   # sadece ad donusumu
    python scripts/remocap_to_g1.py                 # donusum + retarget
"""
import argparse
import re
from pathlib import Path

SRC = Path(r"C:\ufbots_tools\data\throws_bvh")
RENAMED = Path(r"C:\ufbots_tools\data\throws_xsens")
DST = Path(r"C:\ufbots_tools\data\g1_throws")

# ReMoCap adi -> GMR/xsens adi
RENAME = {
    "Hips": "Pelvis",
    "Spine2": "Chest",
    "LeftUpLeg": "Left_UpperLeg", "LeftLeg": "Left_LowerLeg", "LeftFoot": "Left_Foot",
    "RightUpLeg": "Right_UpperLeg", "RightLeg": "Right_LowerLeg", "RightFoot": "Right_Foot",
    "LeftArm": "Left_UpperArm", "LeftForeArm": "Left_Forearm", "LeftHand": "Left_Hand",
    "RightArm": "Right_UpperArm", "RightForeArm": "Right_Forearm", "RightHand": "Right_Hand",
}


def rename_bvh(src: Path, dest: Path) -> int:
    """BVH hiyerarsisindeki eklem adlarini GMR'nin bekledigi adlara cevirir."""
    txt = src.read_text(errors="replace")
    n = 0
    for old, new in RENAME.items():
        # sadece ROOT/JOINT satirlarindaki tam kelime eslesmesi
        pat = re.compile(rf"^(\s*(?:ROOT|JOINT)\s+){re.escape(old)}\s*$", re.M)
        txt, k = pat.subn(rf"\g<1>{new}", txt)
        n += k
    dest.write_text(txt)
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rename-only", action="store_true")
    ap.add_argument("--src", default=str(SRC))
    args = ap.parse_args()

    src = Path(args.src)
    files = sorted(src.glob("*.bvh"))
    if not files:
        raise SystemExit(f"BVH yok: {src}")

    RENAMED.mkdir(parents=True, exist_ok=True)
    print(f"{len(files)} dosya — eklem adlari donusturuluyor\n")
    for f in files:
        k = rename_bvh(f, RENAMED / f.name)
        print(f"  {f.name:<30} {k}/14 eklem")

    print(f"\n-> {RENAMED}")
    if args.rename_only:
        return

    print("\nRetarget icin:")
    print(f"  cd C:/ufbots_tools/GMR")
    print(f"  python scripts/bvh_to_robot_dataset.py \\")
    print(f"      --src_folder {RENAMED} --tgt_folder {DST} \\")
    print(f"      --robot unitree_g1 --format xsens")


if __name__ == "__main__":
    main()
