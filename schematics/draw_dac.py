"""DAC section, 3.3 V analog version (2026-10-23): XIAO + MCP4728 + output smoothing.
The DAC runs from +3V3_A, so it talks to the XIAO directly - no level shifter (Q2, Q3, R18, R19 removed;
R16/R17 stay as the 4.7k bus pull-ups).
Designators follow 'LED Driver.sch'. BIAS_SEL pin 1 <- DAC_x is the intended wiring.
Power rails are shown as net labels (open dots) rather than drawn wires.
v1 (2026-11-04, from the DAC update-noise tests; new / changed parts in orange):
  C10-C13 1 µF -> 10 µF (16 Hz: zipper noise from ramps −13 dB, measured);
  R16/R17 4.7k to +3V3_A -> 10k to the XIAO's 3V3 (pull-up current off the analog rail);
  R27/R28 220 Ω in series at the XIAO's SDA/SCL pins.
Run: python draw_dac.py -> dac.svg / dac.png"""
import schemdraw
import schemdraw.elements as elm
from schemdraw.elements import IcPin

PIN = 1.5  # pin spacing, so the bus rows line up with the DAC pins
NEW = '#c2410c'   # new / changed for v1

with schemdraw.Drawing(show=False) as d:
    d.config(bgcolor='#fcfcfb', margin=0.6, fontsize=11, unit=2.0)

    # ---- U4: XIAO ESP32-S3 -------------------------------------------------------------
    xiao = elm.Ic(pins=[
        IcPin(name='5V', side='top', slot='1/2'),
        IcPin(name='3V3', side='top', slot='2/2', anchorname='V33'),
        IcPin(name='GND', side='bottom'),
        IcPin(name='D4 (GPIO5)', side='left', slot='2/2', anchorname='D4'),
        IcPin(name='D5 (GPIO6)', side='left', slot='1/2', anchorname='D5'),
        IcPin(name='D0 (GPIO1)', side='right', slot='2/2', anchorname='D0'),
        IcPin(name='D1 (GPIO2)', side='right', slot='1/2', anchorname='D1'),
    ], size=(5.5, 3.5), pinspacing=PIN, leadlen=0.6)

    elm.Line().at(xiao['5V']).up(1.0)
    elm.Dot(open=True).label('XIAO_5V', 'left')
    elm.Line().at(xiao.V33).up(1.0).color(NEW)
    elm.Dot(open=True).label('XIAO_3V3 (output)', 'right').color(NEW)
    elm.Line().at(xiao.GND).down(0.5)
    elm.Ground()
    elm.Label().at((xiao.GND[0] + 0.4, xiao.GND[1] - 0.3)).label('U4  XIAO ESP32-S3', fontsize=11, halign='left')

    # Network I2C to the Central (Wire, slave) on connector J2
    elm.Line().at(xiao.D4).left(2.0)
    elm.Dot(open=True).label('J2 SDA_NET', 'left')
    elm.Line().at(xiao.D5).left(2.0)
    elm.Dot(open=True).label('J2 SCL_NET', 'left')
    elm.Dot(open=True).at((xiao.D5[0] - 2.0, xiao.D5[1] - 1.5)).label('J2 GND', 'left')
    elm.Ground()

    # ---- DAC bus (Wire1), 3.3 V on both sides: 220 Ω series at the XIAO, 10k pull-ups to the XIAO's 3V3 ----
    elm.Resistor().at(xiao.D0).right().label('R27 220Ω', loc='top', fontsize=10).color(NEW)
    elm.Line().right(0.5)
    sda = elm.Dot()
    elm.Resistor().at(sda.center).up().label('R17 10k', loc='bottom', fontsize=10).color(NEW)
    elm.Dot(open=True).label('XIAO_3V3', 'top', fontsize=10).color(NEW)
    elm.Line().at(sda.center).right(4.5)
    elm.Label().at((sda.center[0] + 1.0, sda.center[1] + 0.3)).label('SDA_DAC', fontsize=9, halign='left')
    sda_end = d.here

    elm.Resistor().at(xiao.D1).right().label('R28 220Ω', loc='bottom', fontsize=10).color(NEW)
    elm.Line().right(2.0)
    scl = elm.Dot()
    elm.Resistor().at(scl.center).down().label('R16 10k', loc='top', fontsize=10).color(NEW)
    elm.Dot(open=True).label('XIAO_3V3', 'bottom', fontsize=10).color(NEW)
    elm.Line().at(scl.center).right(3.0)
    elm.Label().at((scl.center[0] + 0.5, scl.center[1] + 0.3)).label('SCL_DAC', fontsize=9, halign='left')

    # ---- U5: MCP4728 ---------------------------------------------------------------------
    dac = elm.Ic(pins=[
        IcPin(name='VDD', pin='1', side='top'),
        IcPin(name='SDA', pin='3', side='left', slot='4/4'),
        IcPin(name='SCL', pin='2', side='left', slot='3/4'),
        IcPin(name='~LDAC', pin='4', side='left', slot='2/4', anchorname='LDAC'),
        IcPin(name='RDY/~BSY', pin='5', side='left', slot='1/4', anchorname='RDY'),
        IcPin(name='VOUTA', pin='6', side='right', slot='4/4'),
        IcPin(name='VOUTB', pin='7', side='right', slot='3/4'),
        IcPin(name='VOUTC', pin='8', side='right', slot='2/4'),
        IcPin(name='VOUTD', pin='9', side='right', slot='1/4'),
        IcPin(name='VSS', pin='10', side='bottom'),
    ], size=(4.5, 6.5), pinspacing=PIN, leadlen=0.6).anchor('SDA').at(sda_end) \
        .label('U5\nMCP4728', 'center', fontsize=11)

    elm.Line().at(dac.LDAC).left(1.0)
    elm.Ground().label('tied low', 'bottom', fontsize=9)
    elm.Line().at(dac.RDY).left(1.0)
    elm.Label().label('NC', loc='left', fontsize=9)
    elm.Line().at(dac.VSS).down(0.5)
    elm.Ground()

    # VDD from the clean analog 3.3 V, decoupled right at the pin
    elm.Line().at(dac.VDD).up(3.5)
    vdd = elm.Dot()
    elm.Dot(open=True).at((vdd.center[0], vdd.center[1] + 0.6)).label('+3V3_A', 'top')
    elm.Line().at(vdd.center).up(0.6)
    elm.Line().at(vdd.center).right(1.5)
    elm.Dot()
    d.push(); elm.Capacitor().down().label('C5\n100nF', loc='bottom', fontsize=10); elm.Ground(); d.pop()
    elm.Line().right(1.5)
    elm.Capacitor().down().label('C6\n10µF', loc='bottom', fontsize=10)
    elm.Ground()

    # ---- Output smoothing, fanned out so the caps don't cross other outputs ------------------
    jogs = {'VOUTA': 3.0, 'VOUTB': 0.75, 'VOUTC': -0.75, 'VOUTD': -3.0}
    for i, (pin, ch) in enumerate([('VOUTA', 'A'), ('VOUTB', 'B'), ('VOUTC', 'C'), ('VOUTD', 'D')]):
        p = dac.absanchors[pin]
        elm.Line().at(p).right(0.5)
        elm.Line().toy(p[1] + jogs[pin])
        elm.Line().right(0.5)
        elm.Resistor().right().label(f'R{20 + i} 1k', fontsize=10)
        n = elm.Dot()
        elm.Line().right(2.0)
        elm.Dot(open=True).label(f'DAC_{ch} → channel {ch}, BIAS_SEL pin 1', 'right', fontsize=10)
        elm.Capacitor().at(n.center).down().label(f'C{10 + i} 10µF', loc='bottom', fontsize=10).color(NEW)
        elm.Ground()

    elm.Label().at((dac.VSS[0], dac.VSS[1] - 6.0)).label(
        'MCP4728 (MSOP-10): default I2C address 0x60, on the XIAO\'s second I2C bus (Wire1: D0 = SDA, D1 = SCL)\n'
        'Runs from +3V3_A, same as the XIAO\'s logic: no level shifter needed.  ~LDAC tied low\n'
        'Reference = VDD (set in firmware) → DAC_x = 0–3.3 V, same range as the trimmer and the U1A clamp → full current.\n'
        '    Internal 2.048 V reference also works: 0.5 mV steps (≈ −5 dB zipper); the bias then tops out at 62% of full scale\n'
        'Smoothing: 1k + 10µF ≈ 16 Hz (ramp zipper −13 dB). R kept at 1k so it barely upsets the difference amp\'s 100k balance\n'
        'Each DAC write adds a click (500 writes/s = a 500 Hz comb): firmware writes only when the value changes.\n'
        'Layout: SDA/SCL short, over unbroken ground, away from J1 / U1A / Vbias / R13; C5/C6 at U5\'s pins;\n'
        '    XIAO / U5 ground returns kept local. XIAO off USB in use (a USB loop adds hum; use a USB isolator for development)',
        fontsize=10)

    d.save('dac.svg', transparent=False)
    d.save('dac.png', transparent=False, dpi=150)
