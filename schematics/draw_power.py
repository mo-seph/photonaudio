"""Power supply - v1 PCB (2026-11-03; 3.3 V analog version from 2026-10-23).
New for v1, drawn in orange: R24 + C17 RC filter between the 12 V input and the analog loads (the 12 V SMPS's
burst-mode line arrives on the rail: the breadboard test removed it as completely as a 9 V battery);
U6 fed from the filtered VLED through R25 + C18 instead of from +5V_D; FB1 in the XIAO's 5 V feed.
U2 (7805) stays on the unfiltered side and only powers the XIAO.
2026-11-04: sized for 4 × 300 mA LEDs (1.2 A): D1 SS14 -> SS34, R24 + R24B (two 2.2 Ω 2512 in parallel), C17 2200 µF.
Designators follow 'LED Driver.sch'; U6, C15, C16 (2026-10-23), R24, R25, C17, C18, FB1 (2026-11-03) and R24B (2026-11-04) are new.
Run: python draw_power.py -> power.svg / power.png"""
import schemdraw
import schemdraw.elements as elm

NEW = '#c2410c'   # new for v1


def shunt_cap(label, polar=True, color='black'):
    """Capacitor from the current point down to ground, label on the right."""
    elm.Capacitor(polar=polar).down().label(label, loc='bottom').color(color)
    elm.Ground()


with schemdraw.Drawing(show=False) as d:
    d.config(bgcolor='#fcfcfb', margin=0.6, fontsize=11, unit=2.5)

    # 12 V in, reverse-polarity diode in series, bulk cap to ground
    elm.Dot(open=True).label('J3 pin 1\n(DC jack, centre +)', 'left')
    elm.Schottky().right().label('D1 B340A (3A, SMA)').color(NEW)
    elm.Dot()
    d.push(); shunt_cap('C1\n470µF 25V'); d.pop()
    elm.Line().right(2.5)
    raw = elm.Dot().label('12V_RAW', 'bottom')
    elm.Line().right(1.5)

    # RC filter: everything analog sits after R24 ∥ R24B (two 2512s share the heat at 1.2 A)
    r24 = elm.Resistor().right().label('R24 2.2Ω\n2512 1W', loc='top').color(NEW)
    elm.Dot().at(r24.start).color(NEW)
    elm.Line().at(r24.start).down(1.8).color(NEW)
    elm.Resistor().right().label('R24B 2.2Ω\n2512 1W', loc='bottom').color(NEW)
    elm.Line().up(1.8).color(NEW)
    elm.Dot().at(r24.end).color(NEW)
    elm.Line().at(r24.end).right(1.0).color(NEW)
    vled = elm.Dot().label('VLED', 'top').color(NEW)
    d.push(); shunt_cap('C17\n2200µF 25V\nlow-ESR', color=NEW); d.pop()
    elm.Line().right(3.0)
    tap = elm.Dot()
    elm.Line().right(13)
    elm.Dot(open=True).label('LED_SUPPLY\n→ R12, every channel', 'right')

    # 5 V for the XIAO only, from the unfiltered side (its WiFi current pulses stay off VLED)
    elm.Line().at(raw.center).up(5.5)
    elm.Line().right(1.5)
    elm.Dot()
    d.push(); shunt_cap('C2\n330nF', polar=False); d.pop()
    elm.Line().right(1.5)
    reg = elm.VoltageRegulator().right().anchor('in').label('U2 LD1117S50\n(XIAO supply)', loc='top', ofst=0.4)
    elm.Ground().at(reg.gnd)
    elm.Line().at(reg.out).right(1.5)
    elm.Dot()
    d.push(); shunt_cap('C3\n10µF', polar=False); d.pop()
    elm.Line().right(2.0)
    elm.Dot().label('+5V_D', 'top')
    elm.Inductor2(loops=2).right().label('FB1 ferrite\n(or 0Ω)', loc='top').color(NEW)
    elm.Schottky().right(3.0).label('D2 SS14', loc='top')
    elm.Dot(open=True).label('XIAO_5V (≈4.7 V)', 'right')

    # 3.3 V analog rail from the filtered VLED, with a second RC ahead of U6
    elm.Resistor().at(tap.center).down().label('R25 22Ω', loc='bottom').color(NEW)
    elm.Line().down(1.5).color(NEW)
    elm.Line().right(1.5).color(NEW)
    elm.Dot().color(NEW)
    d.push(); shunt_cap('C18\n100µF 25V', color=NEW); d.pop()
    elm.Line().right(3.0)
    elm.Dot()
    d.push(); shunt_cap('C15\n100nF 50V', polar=False); d.pop()
    elm.Line().right(1.5)
    reg3 = elm.VoltageRegulator().right().anchor('in').label('U6 LD1117-3.3\n(analog 3.3 V)', loc='top', ofst=0.4)
    elm.Ground().at(reg3.gnd)
    elm.Line().at(reg3.out).right(1.5)
    elm.Dot()
    d.push(); shunt_cap('C16\n10µF'); d.pop()
    elm.Line().right(2)
    a3 = elm.Dot()
    elm.Line().right(3.5)
    elm.Dot(open=True).label('+3V3_A\nop-amps, DAC, R14', 'right')

    # Bias supply filter
    elm.Resistor().at(a3.center).down(4).label('R1 100Ω', loc='bottom')
    elm.Dot()
    d.push(); elm.Line().right(2); elm.Dot(); shunt_cap('C4\n100µF'); d.pop()
    elm.Line().right(3.5)
    elm.Dot(open=True).label('+3V3_BIAS\nbias trimmers', 'right')

    elm.Label().at((-1.0, -3.2)).label('J3 pin 2 → GND\n(pin 3 = switch, unused)', fontsize=9, halign='right')
    elm.Label().at((-1.0, reg3.gnd[1] - 7.0)).label(
        'Orange = new for v1 (2026-11-03/04). Sized for 4 × 300 mA LEDs (1.2 A): supply 12 V, ≥ 2 A.\n'
        'R24 ∥ R24B (1.1 Ω, fit both) + C17: corner 66 Hz, ≈ −34 dB at 3.5 kHz if C17 is low-ESR (≤ 0.03 Ω, ripple ≥ 1.5 A).\n'
        '    Drops 0.44 V at 400 mA (4 × 100 mA); 1.3 V and 0.8 W in each resistor at 1.2 A (4 × 300 mA).\n'
        'R25 + C18 (72 Hz) keep the LED currents\' audio-rate ripple on VLED out of +3V3_A, the DAC\'s reference.\n'
        '    U6 then dissipates ≈ 0.1 W (11.4 V in, ≈ 10 mA). LD1117 max input 15 V: 12 V supplies only.\n'
        'FB1: 0805 ferrite bead, ≥ 500 mA (≈ 600 Ω at 100 MHz), against the XIAO\'s RF; fit 0 Ω if not needed.\n'
        'Ground: one unbroken plane (the XIAO may have its own island, one link). J3 GND, C1, C17 meet at the power entry.\n'
        '    J1 sleeves (via R26) join the main plane at their jacks. U5 (DAC) on the main plane, beside the island link.\n'
        '    Keep U2 / XIAO return currents away from U1 pin 4 and R13: any mV between them becomes LED current (1/R13 per mV).\n'
        '    Route each channel\'s LED return (R13 bottom) to the power entry; VLED trunk and returns ≥ 1.5 mm or pours (1.2 A).\n'
        'LD1117 in TO-220 is pinned GND, OUT, IN - not like a 7805 (IN, GND, OUT). It needs ≥ 10 µF on its output (C16).\n'
        'Breadboard: D1 can be left out (no noise role), but then a reversed supply destroys C1 / C17.',
        fontsize=10, halign='left')
    d.save('power.svg', transparent=False)
    d.save('power.png', transparent=False, dpi=150)
