"""Build-and-test stages for the Quad LED Driver Board v1.0.

Designators are the board's (Quad LED Driver Board.brd, 2026-11-07 14:36).
Strip A uses the "2" names (U8, U7, R40-R53 ...), B the "1" names, C the "3"
names and D the plain names (U1, U3, R2-R15 ...). Strip B-D parts are found
from strip A's by position (24 mm pitch).
"""

# ------------------------------------------------------------------ parts
# (ref, value, part / package, note)  -- note: orientation or why
POWER = [
    ("C2", "330 nF", "0805 X7R 50 V", "at VR2's input"),
    ("C15", "100 nF", "0805 X7R 50 V", "at VR1's input"),
    ("R25", "22 Ω", "0805", "feeds VR1 from the LED supply"),
    ("R1", "100 Ω", "1206", "bias-supply filter, with C4"),
    ("FB1", "ferrite bead", "0805, 600 Ω @ 100 MHz, ≥ 1 A", "or a 0 Ω link"),
    ("D3", "B340A", "SMA, 3 A Schottky", "band = cathode, at the upper end"),
    ("D2", "SS14", "SMA, 1 A Schottky", "band = cathode, at the upper end"),
    ("C16", "10 µF tantalum", "3216 (case A)", "band on the part = +, to the pad marked +"),
    ("C3", "10 µF tantalum", "3216 (case A)", "band on the part = +, to the pad marked +"),
    ("R24", "2.2 Ω 1 W", "2512", ""),
    ("R24B", "2.2 Ω 1 W", "2512", "fit both: 1.1 Ω together"),
    ("VR1", "LD1117S33 (3.3 V)", "SOT-223", "the 3.3 V one: don't swap with VR2"),
    ("VR2", "LD1117S50 (5 V)", "SOT-223", "the 5 V one, powers only the XIAO"),
    ("C1", "470 µF 25 V", "SMD can, 10 × 10 mm", "+ is the lower pad; black stripe (−) up"),
    ("C18", "100 µF 25 V", "SMD can, 6.3 mm", "black stripe = −"),
    ("C4", "100 µF 16 V", "SMD can, 6.3 mm", "black stripe = −"),
    ("C17", "2200 µF 25 V", "radial, 7.5 mm pitch", "long leg = +, to the pad marked +"),
    ("PWR_IN", "DC jack", "PJ-102AH, 5.5 × 2.1 mm", "fit last in this stage"),
]

DAC = [
    ("U5", "MCP4728", "MSOP-10, 0.5 mm pitch", "dot = pin 1. Solder it first, check for bridges with a loupe"),
    ("C5", "100 nF", "0805", "at U5 pin 1"),
    ("C6", "10 µF", "1206", ""),
    ("R16", "10 kΩ", "1206", "I2C pull-up to the XIAO's 3V3"),
    ("R17", "10 kΩ", "1206", "I2C pull-up to the XIAO's 3V3"),
    ("R27", "220 Ω", "1206", "series, SDA"),
    ("R28", "220 Ω", "1206", "series, SCL"),
    ("R20", "1 kΩ", "1206", "DAC A filter"),
    ("R21", "1 kΩ", "1206", "DAC B filter"),
    ("R22", "1 kΩ", "1206", "DAC C filter"),
    ("R23", "1 kΩ", "1206", "DAC D filter"),
    ("C10", "10 µF", "1206", "DAC A filter"),
    ("C11", "10 µF", "1206", "DAC B filter"),
    ("C12", "10 µF", "1206", "DAC C filter"),
    ("C13", "10 µF", "1206", "DAC D filter"),
    ("I2C_GND", "0 Ω", "0805", "joins the Qwiic ground"),
    ("I2C", "Qwiic socket", "JST SH 4-pin right-angle (SM04B-SRSS-TB)", "network I2C"),
    ("U4", "XIAO ESP32-S3", "two 1 × 7 female headers", "USB-C towards the top edge. Solder the headers with the XIAO plugged in"),
]

# strip A; the others are mapped by position
CHANNEL_A = [
    ("C27", "100 nF", "0805", "next to U8 pin 8"),
    ("C30", "1 nF C0G", "0805", ""),
    ("C28", "1 µF", "0805", "input cap"),
    ("C29", "1 µF", "0805", "input cap"),
    ("C32", "10 µF", "0805", "trimmer wiper to GND"),
    ("R40", "1 MΩ", "1206", ""),
    ("R41", "1 MΩ", "1206", ""),
    ("R42", "100 kΩ 0.1 %", "1206 thin film", "the four 100k set the hum rejection"),
    ("R43", "100 kΩ 0.1 %", "1206 thin film", ""),
    ("R44", "100 kΩ 0.1 %", "1206 thin film", ""),
    ("R45", "100 kΩ 0.1 %", "1206 thin film", ""),
    ("R46", "10 kΩ", "1206", "set-point divider"),
    ("R47", "1.6 kΩ", "1206", "set-point divider: sets full scale"),
    ("R48", "1 kΩ", "1206", ""),
    ("R49", "220 Ω", "1206", "base resistor"),
    ("R53", "470 kΩ", "1206", "small offset so zero is fully off"),
    ("R51", "4.7 Ω", "1206", "current sense"),
    ("R_LIFT2", "0 Ω", "0805", "input sleeve to ground"),
    ("R_KEL2", "0 Ω", "0805", "Kelvin link, by C17 (not in the strip)"),
    ("U8", "MCP6002", "SOIC-8", "dot = pin 1"),
    ("U7", "BCP56-16", "SOT-223", "big tab is the collector"),
    ("R50", "47 Ω 1 W", "2512", "LED series resistor, runs warm"),
    ("R52", "10 kΩ trimmer", "Bourns 3314J", ""),
    ("BIAS_SEL2", "1 × 3 header", "2.54 mm + jumper", "jumper on POT (lower pair) to start"),
    ("AUDIO_IN2", "3.5 mm jack", "Lumberg 1503 09", "audio input"),
    ("J_LED2", "3.5 mm jack", "Lumberg 1503 09", "LED output: never plug audio in here"),
]
LEAVE_EMPTY_A = [("R12B2", "only for more LED current"), ("R13B2", "only for more LED current"),
                 ("C31", "only with the 100 Ω ground-lift option")]
OPTIONAL_A = [("J_LIFT2", "ground-lift jumper, needs R_LIFT2 = 100 Ω + C31"),
              ("J_DC_HOT2", "DC-coupling link across C29"), ("J_DC_COLD2", "DC-coupling link across C28")]

KEL = {"A": "R_KEL2", "B": "R_KEL1", "C": "R_KEL3", "D": "R_KEL"}
STRIP_DX = {"A": 0, "B": 24, "C": 48, "D": 72}
BIAS_SEL = {"A": "BIAS_SEL2", "B": "BIAS_SEL1", "C": "BIAS_SEL3", "D": "BIAS_SEL"}


def strip_map(B):
    """Map every strip-A ref to its B / C / D twin by position and value."""
    refs = [r for r, *_ in CHANNEL_A] + [r for r, _ in LEAVE_EMPTY_A] + [r for r, _ in OPTIONAL_A]
    out = {"A": {r: r for r in refs}}
    for X in "BCD":
        dx = STRIP_DX[X]
        m = {}
        for r in refs:
            if r.startswith("R_KEL"):
                m[r] = KEL[X]
                continue
            ea = B.elements[r]
            best, bd = None, 1e9
            for e in B.elements.values():
                if e["package"] != ea["package"] or e["value"] != ea["value"] or e["name"] == r:
                    continue
                d = abs(e["x"] - (ea["x"] + dx)) + abs(e["y"] - ea["y"])
                if d < bd:
                    best, bd = e["name"], d
            assert bd < 3.0, (r, X, best, bd)
            m[r] = best
        assert len(set(m.values())) == len(m), X
        out[X] = m
    return out


def channel_parts(B, X):
    sm = strip_map(B)[X]
    rows = []
    for r, v, p, n in CHANNEL_A:
        ref = sm[r]
        note = n.replace("U8", sm["U8"]).replace("C29", sm["C29"]).replace("C28", sm["C28"])
        rows.append((ref, v, p, note))
    return rows, sm


# ------------------------------------------------------------------ tests
# Each test: (what to do, where to probe, what to expect)
S0_TESTS = [
    ("Look at the slots in the jack and DC-jack pads", "AUDIO_IN, J_LED, PWR_IN", "copper inside each slot (plated)"),
    ("Resistance: 12 V input to GND", "PWR_IN centre pin ↔ T_G2", "open (OL)"),
    ("Resistance: LED supply to GND", "T_LS ↔ T_G1", "open"),
    ("Resistance: 3.3 V rail to GND", "T_3V3 ↔ T_G3", "open"),
    ("Resistance: 5 V rail to GND", "T_5V ↔ T_G", "open"),
    ("The old short: LED supply to each strip's collector", "T_LS ↔ J_LED sleeve pad, strips A-D", "open on all four"),
    ("The other old short: bias supply to DAC B", "C4 + pad ↔ C11 upper pad", "open"),
    ("Ground test points are one net", "T_G ↔ T_G1 ↔ T_G2 ↔ T_G3", "≈ 0 Ω"),
]

S1_TESTS = [
    ("Before power: resistance 12 V in to GND", "PWR_IN centre pin ↔ T_G2", "climbs as the caps charge, ends > 1 kΩ"),
    ("Bench supply 12 V, current limit 100 mA, switch on", "supply's current display", "10-20 mA once the caps have charged"),
    ("Input after the polarity diode", "C1 + pad (12V_RAW)", "11.6-11.85 V"),
    ("LED supply", "T_LS", "same as C1 + (within 0.05 V)"),
    ("3.3 V regulator input", "C18 + pad", "≈ 0.1 V below T_LS"),
    ("Analog 3.3 V rail", "T_3V3", "3.24-3.36 V"),
    ("Bias supply", "C4 + pad (3V3_BIAS)", "same as T_3V3"),
    ("5 V regulator output", "C3 + pad (5V_RAW)", "4.90-5.10 V"),
    ("5 V after the ferrite", "T_5V", "same as C3 +"),
    ("XIAO 5 V, after D2 (no XIAO yet)", "D2 upper pad (cathode)", "≈ 4.8-5 V (no load)"),
    ("VR1, VR2, D3 after a minute", "finger", "cold"),
    ("Optional: reverse the supply leads (limit 50 mA)", "supply's current display", "≈ 0 mA, all rails 0 V"),
]

S2_TESTS = [
    ("Before power: jumper on POT, trimmer anywhere, nothing plugged in", "BIAS_SEL2", "jumper on the lower pair (POT)"),
    ("Current limit 200 mA, 12 V on", "supply's current display", "as stage 1 (≈ 15 mA)"),
    ("Op-amp supply", "U8 pin 8 (or T_3V3)", "3.24-3.36 V"),
    ("Turn the trimmer to one end, then the other", "BIAS_SEL2 middle pin (Vbias)", "0 V at one end, ≈ 3.27 V at the other. Note which way is 0"),
    ("Op-amp A output, trimmer at mid", "T_01", "= Vbias, within ±10 mV"),
    ("Op-amp A inputs", "T_O2 and T_O3", "equal to each other, ≈ 0.92 × Vbias"),
    ("Set point", "T_O5", "0.138 × Vbias (0.45 V at full)"),
    ("Trimmer to 0, then plug the LED into J_LED2", "LED", "off"),
    ("Turn the trimmer up slowly", "T_EM (+) and T_KG (−)", "rises smoothly; LED current = V ÷ 4.7 Ω"),
    ("Trimmer at full", "T_EM ↔ T_KG", "≈ 0.44 V (≈ 94 mA)"),
    ("Op-amp B output at full", "T_O7", "≈ 1.2-1.6 V. At 3.3 V with the LED dim: check U7"),
    ("LED anode at full", "T_LT", "≈ T_LS − 4.4 V"),
    ("Supply current at full", "supply's current display", "stage-1 current + ≈ 94 mA"),
    ("After 2 minutes at full", "U7 and R50", "warm, not too hot to touch"),
    ("Mid brightness, idle", "T_EM ↔ T_KG", "steady reading; no whine in the pickup"),
    ("Audio: interface line out → AUDIO_IN2, trimmer at mid, 1 kHz sine, raise slowly", "pickup / ears", "clean until ±1.65 V peak, then clips flat"),
    ("No signal, input plugged in", "pickup", "no hum; compare TRS and TS leads"),
]

S3_TESTS = [
    ("XIAO out, jumper on POT. 12 V on (limit 300 mA)", "supply's current display", "as stage 2 (≈ 15 mA plus the LED)"),
    ("DAC doesn't get warm", "U5, finger", "cold"),
    ("3.3 V rail still good", "T_3V3", "3.24-3.36 V"),
    ("12 V off. Fit the XIAO (USB-C to the top edge). 12 V on", "supply's current display", "up by ≈ 30-60 mA; the XIAO boots"),
    ("XIAO 5 V pin", "U4 pin 14", "≈ 4.6-4.8 V"),
    ("I2C lines idle", "T_SD, T_SC", "≈ 3.3 V"),
    ("Plug in USB (12 V still on)", "XIAO", "nothing changes; USB enumerates"),
    ("Flash dac_test, env xiao-s3-board; open the monitor", "serial monitor", "\"network slave 0x13 started\", \"device at 0x60 (MCP4728)\""),
    ("check 10000", "serial monitor", "0 write, 0 read failures, 0 wrong values"),
    ("a 4095, a 2048, a 0", "T_DA", "≈ 3.3 V, 1.65 V, 0 V"),
    ("b 4095, c 4095, d 4095", "C11, C12, C13 upper pads", "≈ 3.3 V each"),
    ("Move BIAS_SEL2's jumper to DAC (upper pair); a 4095", "T_EM ↔ T_KG", "≈ 0.44 V, LED at full"),
    ("a 0", "LED", "fully off"),
    ("ramp 4000", "LED", "fades up and down every 4 s"),
    ("Real firmware: I2CElectronics env peripheral-led, -t uploadfs then -t upload", "Central / GUI over the Qwiic socket", "the Central finds the board; LIGHT_1 follows"),
]

S4_TESTS_EACH = [
    ("Jumper on POT, trimmer to 0, LED plugged in, 12 V on (limit 600 mA)", "LED", "off"),
    ("Trimmer sweep", "Vbias on the header's middle pin", "0 → ≈ 3.27 V"),
    ("Trimmer at full", "across the 4.7 Ω sense resistor", "≈ 0.44 V (≈ 94 mA)"),
    ("Jumper to DAC; b / c / d 4095, then 0", "sense resistor, LED", "full, then fully off"),
    ("Audio through the channel", "pickup", "as strip A"),
]
S4_TESTS_ALL = [
    ("All four channels at full", "supply's current display", "≈ 0.45 A"),
    ("LED supply under full load", "T_LS", "≈ 11.2 V"),
    ("Crosstalk: audio into A, B-D steady", "sense resistors of B-D (AC mV) / pickups", "B-D don't move with A's audio"),
    ("After 5 minutes, all at full", "R24 / R24B, VR2, every U7-twin", "warm at most"),
]
