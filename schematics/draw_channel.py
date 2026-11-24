"""One LED driver channel (two op-amp version), 3.3 V analog supply (2026-10-23).
Designators match 'LED Driver.sch'. Changes from the 5 V version: U1, R14 and the trimmer
run from 3.3 V; R9 1k -> 1.6k; R14 1M -> 470k.
v1 (2026-11-03): C9 100 pF -> 1 nF (as on the breadboard: more phase margin, no audio effect);
J1 sleeve to GND through a ground-lift footprint, R26 (0 Ω, or 100 Ω with C19 10 nF across it).
2026-11-04, up to 300 mA LEDs: R13B in parallel with R13 sets the range (not fitted = 97 mA, 2.2 Ω = 303 mA);
R12B in parallel with R12 shares the heat; R11 470 -> 220 Ω for the base current; C20 10 µF at the trimmer
wiper (keeps Vbias low-impedance at hum frequencies, like C10 does for the DAC).
New / changed parts in orange.
Run: python draw_channel.py -> channel.svg / channel.png"""
import schemdraw
import schemdraw.elements as elm

NEW = '#c2410c'   # new / changed for v1


def pin_label(at, text, dx=0.0, dy=0.3):
    elm.Label().at((at[0] + dx, at[1] + dy)).label(text, fontsize=8)


with schemdraw.Drawing(show=False) as d:
    d.config(bgcolor='#fcfcfb', margin=0.6, fontsize=11, unit=2.2)

    # ---- U1A: balanced difference amp, reference = Vbias --------------------------
    # flip(): + (in2) on top, − (in1) on bottom
    op1 = elm.Opamp(leads=True).flip().label('U1A', loc='center', ofst=(-0.3, 0), fontsize=10)
    pin_label(op1.in2, 'pin 3')
    pin_label(op1.in1, 'pin 2', dy=-0.6)
    pin_label(op1.out, 'pin 1', dx=-0.6)

    # Tip (hot) -> C8 -> R5 -> +   (R2 = 1M bleed)
    elm.Line().at(op1.in2).left(0.75)
    np = elm.Dot()
    elm.Resistor().left().label('R5 100k')
    elm.Dot()
    d.push(); elm.Resistor().down().label('R2 1M', loc='bottom'); elm.Ground(); d.pop()
    elm.Capacitor().left().label('C8 1µF\n(JP4 across = DC)')
    elm.Dot(open=True).label('J1 tip', 'left')

    # + input also goes via R7 to Vbias (JP3 centre pin)
    elm.Resistor().at(np.center).up().label('R7 100k', loc='bottom')
    vb = elm.Dot().label('Vbias', 'left')

    # Ring (cold) -> C7 -> R4 -> −   (R3 = 1M bleed)
    elm.Line().at(op1.in1).left(0.75)
    nn = elm.Dot()
    elm.Line().down(2.2)
    elm.Resistor().left().label('R4 100k', loc='bottom')
    elm.Dot()
    d.push(); elm.Resistor().down().label('R3 1M', loc='bottom'); elm.Ground(); d.pop()
    elm.Capacitor().left().label('C7 1µF\n(JP5 across = DC)')
    ring = elm.Dot(open=True).label('J1 ring', 'left')
    elm.Dot(open=True).at((ring.center[0], ring.center[1] - 2.5)).label('J1 sleeve', 'left')
    # Ground-lift footprint: 0 Ω normally; 100 Ω ∥ 10 nF breaks a hum loop through the cable shield
    elm.Line().down(1.0)
    lift = elm.Dot()
    elm.Resistor().down().label('R26 0Ω\n(100Ω to lift)', loc='top')
    lifted = elm.Dot()
    elm.Ground()
    elm.Line().at(lift.center).right(1.5)
    elm.Capacitor().down().label('C19 10nF\n(only with 100Ω)', loc='bottom')
    elm.Line().tox(lifted.center)
    elm.Label().at((ring.center[0] - 2.6, ring.center[1] - 8.6)).label(
        'J1 tip and ring switch (NC) pins → the J1 sleeve net (above R26):\n'
        'an unplugged input is shorted, so the channel idles silently.\n'
        'Sleeve switch pin: not connected', fontsize=9, halign='left').color(NEW)

    # Feedback: R6 from output to − input
    elm.Line().at(nn.center).down(1.1)
    elm.Resistor().right().tox(op1.out).label('R6 100k', loc='bottom')
    elm.Line().toy(op1.out)

    # ---- Bias select: BIAS_SEL (3-pin jumper) picks trimmer R15 or the DAC -------------
    elm.Line().at(vb.center).up(0.6)
    sw = elm.SwitchSpdt2(action=None).up().anchor('a')
    elm.Label().at((sw.a[0] - 0.4, sw.a[1] + 0.4)).label(
        'BIAS_SEL (3-pin jumper)\n1 = DAC\n2 = Vbias\n3 = trimmer', fontsize=9, halign='right')
    # right throw -> trimmer wiper
    elm.Line().at(sw.c).up(0.6)
    elm.Line().right(1.0)
    elm.Dot().color(NEW)
    d.push(); elm.Capacitor().down().label('C20\n10µF', loc='bottom', fontsize=10).color(NEW); elm.Ground(); d.pop()
    elm.Line().right(1.0)
    pot = elm.Potentiometer().up().anchor('tap').label('R15 10k\ntrimmer', loc='bottom')
    elm.Line().at(pot.end).up(0.3)
    elm.Dot(open=True).label('+3V3_BIAS', 'right')
    elm.Ground().at(pot.start)
    # left throw -> DAC output
    elm.Line().at(sw.b).up(1.4)
    elm.Dot(open=True).label('DAC_A (B, C, D on\nthe other channels)', 'left')

    # ---- Divider R8/R9 -----------------------------------------------------------------
    elm.Line().at(op1.out).right(0.5)
    elm.Dot().label('V1', 'bottom', fontsize=10)
    elm.Resistor().right().label('R8 10k')
    elm.Dot().label('Vctrl', 'top', fontsize=10)
    d.push(); elm.Resistor().down().label('R9 1.6k', loc='top'); elm.Ground(); d.pop()
    elm.Line().right(1)

    # ---- U1B + Q1: current sink -------------------------------------------------------
    op2 = elm.Opamp(leads=True).flip().anchor('in2').label('U1B', loc='center', ofst=(-0.3, 0), fontsize=10)
    pin_label(op2.in2, 'pin 5')
    pin_label(op2.in1, 'pin 6', dy=-0.6)
    pin_label(op2.out, 'pin 7', dx=-0.6)
    elm.Resistor().at(op2.out).right().label('R11 220Ω', color=NEW).color(NEW)
    q1 = elm.BjtNpn().anchor('base').label('U3\nBCP56-16\n(tab = C)', 'right')

    # Collector -> LED (off-board on JP2) -> R12 ∥ R12B -> LED_SUPPLY
    elm.LED().at(q1.collector).up().reverse().label('LED connector\npin 1 = anode\npin 2 = cathode', loc='bottom', fontsize=9)
    r12 = elm.Resistor().up().label('R12 47Ω\n2512 1W', loc='bottom')
    elm.Dot(open=True).label('LED_SUPPLY', 'right')
    elm.Dot().at(r12.start).color(NEW)
    elm.Line().at(r12.start).left(1.8).color(NEW)
    elm.Resistor().up().label('R12B\n(not fitted;\n300 mA: both 33Ω)', loc='top', fontsize=9).color(NEW)
    elm.Line().right(1.8).color(NEW)
    elm.Dot().at(r12.end).color(NEW)

    # Emitter -> R13 ∥ R13B -> GND (R13B sets the range)
    elm.Line().at(q1.emitter).down(0.5)
    ne = elm.Dot()
    elm.Line().down(0.5)
    r13 = elm.Resistor().down().label('R13 4.7Ω\n1206', loc='bottom')
    elm.Ground()
    elm.Dot().at(r13.start).color(NEW)
    elm.Line().at(r13.start).right(2.8).color(NEW)
    elm.Resistor().down().label('R13B (not fitted)\nsets the range:\n2.2Ω → 303 mA', loc='bottom', fontsize=9).color(NEW)
    elm.Line().left(2.8).color(NEW)
    elm.Dot().at(r13.end).color(NEW)

    # R10 emitter -> − input, C9 output -> − input
    elm.Line().at(op2.in1).left(0.5)
    elm.Dot()
    elm.Line().down(1.0)
    elm.Dot()
    d.push()
    elm.Capacitor().right().tox(op2.out).label('C9 1nF', loc='bottom', fontsize=10)
    elm.Line().toy(op2.out)
    elm.Dot()
    d.pop()
    elm.Line().down(1.6)
    corner = elm.Dot()
    elm.Resistor().right().tox(ne.center[0] - 1.2).label('R10 1k', loc='bottom')
    elm.Line().toy(ne.center)
    elm.Line().tox(ne.center)

    # R14: lifts pin 6 by ~7 mV so a zero command turns U3 fully off (beats the op-amp's offset)
    elm.Resistor().at(corner.center).down().label('R14 470k', loc='top')
    elm.Dot(open=True).label('+3V3_A', 'bottom')

    # ---- U1 power pins ------------------------------------------------------------------
    bx, by = op1.out[0] - 2, op1.out[1] - 8.0
    elm.Dot(open=True).at((bx, by)).label('+3V3_A → U1 pin 8', 'left')
    elm.Capacitor().down().label('C14\n100nF', loc='bottom')
    elm.Ground().label('U1 pin 4', 'left', ofst=0.6)

    elm.Label().at((op2.out[0] + 0.5, by - 0.5)).label(
        'V1 = Vbias + (tip − ring), clipped to 0–3.3 V by U1\n'
        'Vctrl = V1 × R9/(R8+R9) = V1 / 7.25  (3.3 V → 0.455 V)\n'
        'I_LED = (Vctrl − 7 mV) / (R13 ∥ R13B)  (≈ 95 mA max; R13B 2.2Ω → ≈ 300 mA)\n'
        'R14 adds the 7 mV, so a zero command really is off\n'
        'U1 must be MCP6002 (an LM358 can\'t run on 3.3 V).\n'
        'Audio full swing: ±1.65 V peak around mid bias\n'
        'Kelvin: take U1\'s ground (pin 4, R9, C14) from R13\'s bottom pad;\n'
        'route the LED return from there to the power entry on its own',
        fontsize=10)

    d.save('channel.svg', transparent=False)
    d.save('channel.png', transparent=False, dpi=150)
