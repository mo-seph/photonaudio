"""Supply filter test (2026-11-03): RC between the 12 V input and the analog loads, to see whether the
SMPS burst-mode line (3.5 kHz at code 250, moving with LED current) arrives on the rail.
R24 and C17 are new designators (next free), so they can carry over to the v1 PCB.
Run: python draw_supply_filter.py -> supply_filter.svg / supply_filter.png"""
import schemdraw
import schemdraw.elements as elm

NEW = '#c2410c'   # new parts


def shunt_cap(label, polar=True, color='black'):
    """Capacitor from the current point down to ground, label on the right."""
    elm.Capacitor(polar=polar).down().label(label, loc='bottom').color(color)
    elm.Ground()


with schemdraw.Drawing(show=False) as d:
    d.config(bgcolor='#fcfcfb', margin=0.6, fontsize=11, unit=2.5)

    elm.Dot(open=True).label('J3 pin 1\n12 V supply +', 'left')
    elm.Schottky().right().label('D1 SS14')
    elm.Dot()
    d.push(); shunt_cap('C1\n470µF'); d.pop()
    elm.Line().right(1.5)
    raw = elm.Dot().label('12 V raw', 'bottom')
    elm.Line().right(1.5)
    elm.Resistor().right().label('R24  10Ω  (test)\n2.2Ω 1206 on PCB', loc='top').color(NEW)
    elm.Line().right(1.5).color(NEW)
    f = elm.Dot().label('VLED', 'top').color(NEW)
    d.push(); shunt_cap('C17\n1000µF 35V\n+ to VLED', color=NEW); d.pop()
    elm.Line().right(4)
    led = elm.Dot()
    elm.Line().right(3)
    elm.Dot(open=True).label('→ R12 → LED → U3\n(LED_SUPPLY)', 'right')
    elm.Line().at(led.center).down(3)
    elm.Line().right(3)
    elm.Dot(open=True).label('→ U6 LD1117 IN\n(+3V3_A: op-amps, DAC)', 'right')

    # anything digital stays on the unfiltered side
    elm.Line().at(raw.center).up(2.5)
    elm.Dot(open=True).label('U2 7805, if fitted\n(stays before R24)', 'right')

    elm.Label().at((-1.2, -3.4)).label('J3 pin 2 → GND', fontsize=9, halign='right')
    elm.Label().at((0, f.center[1] - 5.4)).label(
        'Breadboard: lift the link from C1 to the VLED rail and fit R24 in its place.\n'
        'C17 from the VLED rail to GND: + leg to the rail, − leg to the supply\'s GND wire (with C1),\n'
        'not at R13 / U1 pin 4, so its ripple current goes back to the supply, not through the analog ground.\n'
        'R24 10Ω: corner 16 Hz, −47 dB at 3.5 kHz; drops ~0.25 V at ~25 mA. Fine at the housing\'s low bias -\n'
        'not above ~code 2000 (at 100 mA it drops 1 V and eats the LED headroom).\n'
        'PCB: 2.2Ω 1206 + 1000µF: corner 72 Hz, −34 dB at 3.5 kHz, ~0.24 V at 110 mA.',
        fontsize=10, halign='left')
    d.save('supply_filter.svg', transparent=False)
    d.save('supply_filter.png', transparent=False, dpi=150)
