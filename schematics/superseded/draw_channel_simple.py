"""Simplest LED driver channel: one op-amp + one transistor.
Run: python draw_channel_simple.py -> channel_simple.svg / channel_simple.png"""
import schemdraw
import schemdraw.elements as elm

with schemdraw.Drawing(show=False) as d:
    d.config(fontsize=11, unit=2.2)

    # Current sink op-amp: flip() puts + (in2) on top, − (in1) on bottom
    op = elm.Opamp(leads=True).flip().label('U1A\nMCP6002', loc='center', ofst=(-0.3, 0), fontsize=9)

    # Vctrl node: bias + audio summed by resistors, scaled down by R3
    elm.Line().at(op.in2).left(1.5)
    n = elm.Dot().label('Vctrl', 'top', ofst=(0.5, 0))
    d.push(); elm.Resistor().down().label('R3 10k', loc='top'); elm.Ground(); d.pop()

    # Bias pot -> R1 -> Vctrl
    elm.Resistor().at(n.center).up().label('R1 100k', loc='bottom')
    elm.Line().up(1.5)
    top = elm.Dot().label('Vbias\n(later: DAC\noutput here)', 'left')
    elm.Line().right(1.5)
    pot = elm.Potentiometer().up().anchor('tap').label('BIAS\n10k lin', loc='bottom')
    elm.Line().at(pot.end).up(0.5)
    elm.Dot(open=True).label('+5V_BIAS', 'right')
    elm.Ground().at(pot.start)

    # Audio in -> C1 -> R2 -> Vctrl
    elm.Resistor().at(n.center).left().label('R2 100k')
    elm.Capacitor().left().label('C1 1µF film')
    j = elm.Dot()
    d.push(); elm.Resistor().down().label('R4 1M', loc='bottom'); elm.Ground(); d.pop()
    elm.Line().left(1)
    tip = elm.Dot(open=True).label('IN tip', 'left')
    elm.Dot(open=True).at((tip.center[0], tip.center[1] - 3.2)).label('IN sleeve', 'left')
    elm.Ground()

    # Op-amp -> base resistor -> transistor
    elm.Resistor().at(op.out).right().label('R5 470Ω')
    q1 = elm.BjtNpn().anchor('base').label('Q1\nBD139', 'right')

    # Collector -> LED -> R10 -> VLED
    elm.LED().at(q1.collector).up().reverse().label('LED 10 mm', loc='bottom')
    elm.Resistor().up().label('R10 68Ω 2W\n(current ceiling)', loc='bottom')
    elm.Dot(open=True).label('VLED +12 V', 'right')

    # Emitter -> Rs -> GND
    elm.Line().at(q1.emitter).down(0.5)
    e = elm.Dot()
    elm.Line().down(0.5)
    elm.Resistor().down().label('R6 Rs 4.7Ω', loc='bottom')
    elm.Ground()

    # Feedback: emitter straight back to − input
    elm.Line().at(op.in1).left(0.5)
    elm.Dot()
    elm.Line().down(2.0)
    elm.Line().right().tox(e.center[0] - 1.2)
    elm.Line().toy(e.center)
    elm.Line().tox(e.center)

    elm.Label().at((op.out[0] - 1, op.out[1] - 7.0)).label(
        'Vctrl = (Vbias + audio) / 12      I_LED = Vctrl / 4.7Ω\n'
        'bias pot: 0 → 5 V gives 0 → ~89 mA idle;  audio ±2.5 V peak swings ±44 mA\n'
        'R10 limits the most the LED can ever get to ~110 mA, whatever the input does\n'
        'MCP6002 (DIP-8): 1 OUT A, 2 −IN A, 3 +IN A, 4 GND, 8 +5V (100 nF pin 8 → GND);  B half = 2nd channel\n'
        'BD139 (label facing you, legs down): E  C  B',
        fontsize=10)

    d.save('channel_simple.svg')
    d.save('channel_simple.png', dpi=150)
