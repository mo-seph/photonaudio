"""Render every picture for the build plan into build_plan/img/.

Run from anywhere:  python3 make_images.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import brd      # noqa: E402
import render   # noqa: E402
import stages as S  # noqa: E402

BRD = os.path.join(HERE, "..", "schematics", "Quad LED Driver Board.brd")
OUT = os.path.join(HERE, "img")


def short(v):
    return v.replace(" (3.3 V)", "").replace(" (5 V)", "")


def labels_for(rows, B):
    return {r: [f"{r}  {short(v)}"] for r, v, *_ in rows}


def tp(B, name):
    p = B.elements[name]["pads"][0]
    return p["x"], p["y"]


def pd(B, el, pad):
    p = B.pad(el, pad)
    return p["x"], p["y"]


def main():
    os.makedirs(OUT, exist_ok=True)
    B = brd.Board(BRD)
    sm = S.strip_map(B)
    f = lambda n: os.path.join(OUT, n)

    s1 = [r for r, *_ in S.POWER]
    s3 = [r for r, *_ in S.DAC]
    sA = [sm["A"][r] for r, *_ in S.CHANNEL_A]
    strips = {X: [sm[X][r] for r, *_ in S.CHANNEL_A] for X in "BCD"}
    empty = {X: [sm[X][r] for r, _ in S.LEAVE_EMPTY_A] for X in "ABCD"}
    full = (0, 0, 170, 100)

    # ---- stage 0: bare-board checks
    probes0 = [
        (*pd(B, "PWR_IN", "1"), ["PWR_IN centre", "↔ T_G2: open"]),
        (*tp(B, "T_G2"), ["T_G2  GND"]),
        (*tp(B, "T_LS"), ["T_LS ↔ T_G1: open"]),
        (*tp(B, "T_G1"), ["T_G1  GND"]),
        (*tp(B, "T_3V3"), ["T_3V3 ↔ T_G3: open"]),
        (*tp(B, "T_G3"), ["T_G3  GND"]),
        (*tp(B, "T_5V"), ["T_5V ↔ T_G: open"]),
        (*tp(B, "T_G"), ["T_G  GND"]),
        (*pd(B, "C4", "+"), ["C4 +"]),
        (*pd(B, "C11", "2"), ["C11 upper", "↔ C4 +: open"]),
    ]
    for X in "ABCD":
        probes0.append((*pd(B, sm[X]["J_LED2"], "1"), [f"{X}: sleeve ↔ T_LS", "open"]))
    render.draw(B, (-1, -8, 171, 101), f("s0_checks.png"), ppm=9, dim=False, probes=probes0,
                label_mm=1.9)

    # ---- stage 1: power
    v1 = (-0.5, 8, 64, 69)
    render.draw(B, full, f("s1_overview.png"), ppm=9, stage=s1, region=v1)
    render.draw(B, v1, f("s1_build.png"), ppm=20, stage=s1, labels=labels_for(S.POWER, B))
    probes1 = [
        (*pd(B, "PWR_IN", "1"), ["PWR_IN centre", "12 V in"]),
        (*pd(B, "C1", "1"), ["C1 +  12V_RAW", "11.6–11.85 V"]),
        (*tp(B, "T_LS"), ["T_LS  LED supply", "= C1 +"]),
        (*tp(B, "T_G1"), ["T_G1  GND", "black probe"]),
        (*pd(B, "C18", "+"), ["C18 +  VR1 in", "≈ T_LS − 0.1 V"]),
        (*tp(B, "T_3V3"), ["T_3V3", "3.24–3.36 V"]),
        (*pd(B, "C4", "+"), ["C4 +  3V3_BIAS", "= T_3V3"]),
        (*pd(B, "C3", "+"), ["C3 +  5V_RAW", "4.90–5.10 V"]),
        (*tp(B, "T_5V"), ["T_5V", "= C3 +"]),
        (*pd(B, "D2", "C"), ["D2 cathode", "XIAO 5 V ≈ 4.8–5 V"]),
        (*tp(B, "T_G"), ["T_G  GND"]),
    ]
    render.draw(B, v1, f("s1_probe.png"), ppm=20, fitted=s1, probes=probes1)

    # ---- stage 2: channel A
    vA = (56, -0.5, 104, 100.5)
    render.draw(B, full, f("s2_overview.png"), ppm=9, stage=sA, fitted=s1, dnf=empty["A"],
                region=vA)
    labA = labels_for([(sm["A"][r], v) for r, v, *_ in S.CHANNEL_A if r != "R_KEL2"], B)
    render.draw(B, vA, f("s2_build.png"), ppm=18, stage=[r for r in sA if r != "R_KEL2"],
                fitted=s1, dnf=empty["A"], labels=labA)
    vK = (24, 0, 74, 18)
    render.draw(B, vK, f("s2_star.png"), ppm=24, stage=["R_KEL2"], fitted=s1,
                labels={"R_KEL2": ["R_KEL2  0 Ω  · strip A"]}, label_mm=1.5)
    vAp = (44, 0, 100, 70)
    probes2 = [
        (*pd(B, "BIAS_SEL2", "2"), ["BIAS_SEL2 middle", "Vbias 0–3.27 V"]),
        (*tp(B, "T_01"), ["T_01  op-amp A out", "= Vbias ±10 mV"]),
        (*tp(B, "T_O2"), ["T_O2  input", "≈ 0.92 × Vbias"]),
        (*tp(B, "T_O3"), ["T_O3  input", "≈ 0.92 × Vbias"]),
        (*tp(B, "T_O5"), ["T_O5  set point", "0.138 × Vbias"]),
        (*tp(B, "T_EM"), ["T_EM  sense +", "full ≈ 0.44 V"]),
        (*tp(B, "T_KG"), ["T_KG  sense −"]),
        (*tp(B, "T_O7"), ["T_O7  op-amp B out", "≈ 1.2–1.6 V at full"]),
        (*tp(B, "T_LT"), ["T_LT  LED anode", "≈ T_LS − 4.4 V at full"]),
        (*tp(B, "T_LS"), ["T_LS  LED supply"]),
        (*tp(B, "T_G1"), ["T_G1  GND"]),
    ]
    render.draw(B, vAp, f("s2_probe.png"), ppm=18, fitted=s1 + sA, probes=probes2)

    # ---- stage 3: XIAO + DAC
    v3 = (-0.5, 58, 70, 100.5)
    render.draw(B, full, f("s3_overview.png"), ppm=9, stage=s3, fitted=s1 + sA, dnf=empty["A"],
                region=v3)
    lab3 = labels_for([row for row in S.DAC if row[0] not in
                       ("R20", "R21", "R22", "R23", "C10", "C11", "C12", "C13")], B)
    lab3[("R20", "R21", "R22", "R23")] = ["R20–R23  1 kΩ"]
    lab3[("C10", "C11", "C12", "C13")] = ["C10–C13  10 µF"]
    render.draw(B, v3, f("s3_build.png"), ppm=20, stage=s3, fitted=s1 + sA, dnf=empty["A"],
                labels=lab3)
    probes3 = [
        (*tp(B, "T_SD"), ["T_SD  SDA", "≈ 3.3 V idle"]),
        (*tp(B, "T_SC"), ["T_SC  SCL", "≈ 3.3 V idle"]),
        (*tp(B, "T_DA"), ["T_DA  DAC A", "code ÷ 4095 × 3.3 V"]),
        (*pd(B, "C11", "2"), ["C11 upper  DAC B"]),
        (*pd(B, "C12", "2"), ["C12 upper  DAC C"]),
        (*pd(B, "C13", "2"), ["C13 upper  DAC D"]),
        (*tp(B, "T_3V3"), ["T_3V3", "3.24–3.36 V"]),
        (*tp(B, "T_5V"), ["T_5V", "≈ 5 V"]),
        (*pd(B, "U4", "14"), ["U4 pin 14", "XIAO 5 V ≈ 4.6–4.8 V"]),
        (*tp(B, "T_G3"), ["T_G3  GND"]),
    ]
    render.draw(B, v3, f("s3_probe.png"), ppm=20, fitted=s1 + s3, probes=probes3)

    # ---- stage 4: strips B-D
    allBCD = strips["B"] + strips["C"] + strips["D"]
    render.draw(B, full, f("s4_overview.png"), ppm=9, stage=allBCD,
                fitted=s1 + sA + s3, dnf=empty["B"] + empty["C"] + empty["D"])
    for X in "BCD":
        dx = S.STRIP_DX[X]
        v = (56 + dx, -1, 104 + dx, 101)
        lab = labels_for([(sm[X][r], v_) for r, v_, *_ in S.CHANNEL_A if r != "R_KEL2"], B)
        render.draw(B, v, f(f"s4_build_{X}.png"), ppm=18,
                    stage=[r for r in strips[X] if r != S.KEL[X]],
                    fitted=s1 + sA + s3, dnf=empty[X], labels=lab)
    render.draw(B, vK, f("s4_star.png"), ppm=24, stage=[S.KEL[X] for X in "BCD"],
                fitted=s1 + ["R_KEL2"],
                labels={S.KEL[X]: [f"{S.KEL[X]}  0 Ω  · strip {X}"] for X in "BCD"}, label_mm=1.5)
    probes4 = []
    for X in "BCD":
        probes4.append((*pd(B, S.BIAS_SEL[X], "2"), [f"{X}: Vbias", "header middle"]))
        r13 = sm[X]["R51"]
        probes4.append((*pd(B, r13, "2"), [f"{X}: {r13} sense +"]))
        probes4.append((*pd(B, r13, "1"), [f"{X}: {r13} sense −"]))
    render.draw(B, (86, -1, 171, 72), f("s4_probe.png"), ppm=14,
                fitted=s1 + sA + s3 + allBCD, probes=probes4, label_mm=1.6)
    print("images in", OUT)


if __name__ == "__main__":
    main()
