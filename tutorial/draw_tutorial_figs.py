"""Figures for TUTORIAL.md. Run: python draw_tutorial_figs.py (needs schemdraw + matplotlib).
Designators match 'schematics/LED Driver.sch'."""
import math

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import schemdraw
import schemdraw.elements as elm
from schemdraw import flow

INK, INK2, GRID, SURFACE, SERIES = '#0b0b0b', '#52514e', '#e4e3df', '#fcfcfb', '#2a78d6'


# ---- 1. Block diagram -------------------------------------------------------------------
def blocks():
    with schemdraw.Drawing(show=False) as d:
        d.config(bgcolor='#fcfcfb', margin=0.6, fontsize=11, unit=1)
        b1 = flow.Box(w=3.2, h=1.6).label('J1\naudio in\n(tip, ring)')
        elm.Arrow().right(1.2)
        b2 = flow.Box(w=3.2, h=1.6).label('C7, C8\nblock DC')
        elm.Arrow().right(1.2)
        b3 = flow.Box(w=3.8, h=1.6).label('U1A\ndifference amp\n+ bias, 0–5 V clip')
        elm.Arrow().right(1.2).label('V1', 'top')
        b4 = flow.Box(w=3.0, h=1.6).label('R8 / R9\n÷ 11')
        elm.Arrow().right(1.2).label('Vctrl', 'top')
        b5 = flow.Box(w=3.8, h=1.6).label('U1B + U3 + R13\ncurrent sink')
        elm.Arrow().right(1.2).label('I_LED', 'top')
        flow.Box(w=2.4, h=1.6).label('LED')
        bias = flow.Box(w=3.8, h=1.4).at((b3.N[0], b3.N[1] + 2.6)).anchor('S').label('Vbias: trimmer R15\nor DAC (BIAS_SEL)')
        elm.Arrow().at(bias.S).to(b3.N)
        d.save('fig_blocks.png', transparent=False, dpi=150)


# ---- 2. LED current vs voltage (illustrative diode model) ----------------------------------
def led_current(v, i_s, n_vt, r_s):
    """Solve I = Is*exp((V - I*Rs)/nVt) for I by bisection."""
    lo, hi = 0.0, 1.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if i_s * math.exp((v - mid * r_s) / n_vt) > mid:
            lo = mid
        else:
            hi = mid
    return lo


def led_iv():
    n_vt, r_s = 0.09, 2.0
    i_s = 0.1 / math.exp((3.7 - 0.1 * r_s) / n_vt)       # calibrated: 100 mA at 3.7 V
    vs = [2.8 + k * 0.005 for k in range(int((3.85 - 2.8) / 0.005) + 1)]
    ims = [1000 * led_current(v, i_s, n_vt, r_s) for v in vs]

    fig, ax = plt.subplots(figsize=(7, 4.2), dpi=150)
    fig.patch.set_facecolor(SURFACE); ax.set_facecolor(SURFACE)
    ax.plot(vs, ims, color=SERIES, linewidth=2)
    ax.axhline(100, color=INK2, linewidth=1, linestyle=(0, (4, 3)))
    ax.text(2.82, 103, 'LED maximum rating, 100 mA', color=INK2, fontsize=9)
    for v in (3.4, 3.6, 3.7):
        i = 1000 * led_current(v, i_s, n_vt, r_s)
        ax.plot([v], [i], 'o', color=SERIES, markersize=6, markeredgecolor=SURFACE, markeredgewidth=2)
        ax.annotate(f'{v:.1f} V → {i:.0f} mA', (v, i), xytext=(-12, 10), textcoords='offset points',
                    ha='right', color=INK, fontsize=9)
    ax.set_xlim(2.8, 3.85); ax.set_ylim(0, 125)
    ax.set_xlabel('Voltage across the LED (V)', color=INK2)
    ax.set_ylabel('LED current (mA)', color=INK2)
    ax.set_title('LED current vs voltage (illustrative model, not datasheet)', color=INK, fontsize=11, loc='left')
    ax.grid(True, color=GRID, linewidth=0.8); ax.set_axisbelow(True)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    for s in ('left', 'bottom'):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=INK2)
    fig.tight_layout()
    fig.savefig('fig_led_iv.png', facecolor=SURFACE)


# ---- 3. Bare current sink -------------------------------------------------------------------
def sink():
    with schemdraw.Drawing(show=False) as d:
        d.config(bgcolor='#fcfcfb', margin=0.6, fontsize=11, unit=2.2)
        elm.Dot(open=True).label('Vctrl\n(0–0.45 V)', 'left')
        elm.Line().right(1)
        op = elm.Opamp(leads=True).flip().anchor('in2').label('U1B', loc='center', ofst=(-0.3, 0), fontsize=10)
        elm.Line().at(op.out).right(1.2)
        q = elm.BjtNpn().anchor('base').label('U3', 'right')
        elm.LED().at(q.collector).up().reverse().label('LED', loc='bottom')
        elm.Resistor().up().label('R12 47Ω', loc='bottom')
        elm.Dot(open=True).label('LED_SUPPLY (12 V)', 'right')
        elm.Line().at(q.emitter).down(0.5)
        e = elm.Dot().label('emitter = Vctrl', 'right', fontsize=10)
        elm.Resistor().down().label('R13 4.7Ω', loc='bottom')
        elm.Ground()
        elm.Line().at(op.in1).left(0.5)
        elm.Line().down(2.2)
        elm.Line().right().tox(e.center[0] - 1.0)
        elm.Line().toy(e.center)
        elm.Line().tox(e.center)
        elm.Label().at((op.out[0] - 1, op.out[1] - 5.2)).label(
            'U1B holds the emitter at Vctrl,\nso I = Vctrl / R13 through R13 and the LED.',
            fontsize=10)
        d.save('fig_sink.png', transparent=False, dpi=150)


# ---- 4. Difference amp ------------------------------------------------------------------------
def diffamp():
    with schemdraw.Drawing(show=False) as d:
        d.config(bgcolor='#fcfcfb', margin=0.6, fontsize=11, unit=2.2)
        op = elm.Opamp(leads=True).flip().label('U1A', loc='center', ofst=(-0.3, 0), fontsize=10)
        elm.Line().at(op.in2).left(0.75)
        p = elm.Dot().label('V+', 'top', ofst=(0.4, 0))
        elm.Resistor().left().label('R5 100k')
        elm.Dot(open=True).label('tip', 'left')
        elm.Resistor().at(p.center).up().label('R7 100k', loc='bottom')
        elm.Dot(open=True).label('Vbias', 'top')
        elm.Line().at(op.in1).left(0.75)
        n = elm.Dot().label('V−', 'bottom', ofst=(0.4, 0))
        elm.Line().down(2.2)
        elm.Resistor().left().label('R4 100k', loc='bottom')
        elm.Dot(open=True).label('ring', 'left')
        elm.Line().at(n.center).down(1.1)
        elm.Resistor().right().tox(op.out).label('R6 100k', loc='bottom')
        elm.Line().toy(op.out)
        elm.Line().at(op.out).right(1)
        elm.Dot(open=True).label('V1', 'right')
        elm.Label().at((op.out[0] - 2, op.out[1] - 5.2)).label(
            'V1 = Vbias + (tip − ring)    when R4 = R5 = R6 = R7', fontsize=10)
        d.save('fig_diffamp.png', transparent=False, dpi=150)


if __name__ == '__main__':
    blocks(); led_iv(); sink(); diffamp()
