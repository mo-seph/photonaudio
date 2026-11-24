# LEDAudioDriver - parts list (2026-10-04)

Enough to breadboard 2 channels, plus spares.
- **Through-hole column:** what to order now for breadboarding.
- **SMD column (added 2026-10-04):** equivalents for the PCB. Same electrical spec unless noted. Passives are 0805, which is hand-solderable; 0603 is fine if the boards will be machine-assembled.

Ship to: Netherlands. Prefer one EU distributor for the loose parts (TME, Reichelt, Mouser EU or Farnell NL) to keep shipping to one charge.

## Order spec (can be handed to Cowork or used as a cart list)

Rules (breadboard order):
- Order the **through-hole** column only (DIP, TO-92, TO-126, TO-220, axial/radial).
- Substitutes are fine if the spec is met; don't substitute the op-amp with a non-rail-to-rail part.
- If a resistor/capacitor assortment kit covering the common values is cheaper than loose parts, buy the kit instead and only order the odd values loose.
- Report the total incl. VAT and shipping before placing the order.

| # | Part | Through-hole (breadboard) | SMD equivalent (PCB) | Qty | Notes / known prices |
|---|---|---|---|---|---|
| 1 | Op-amp | **MCP6002-I/P** (dual, rail-to-rail I/O, 1.8-6 V, DIP-8) | **MCP6002-I/SN** (SOIC-8). Same pinout. TLV9062 (SOIC-8) is a lower-noise upgrade. | 6 | TME ~£0.31-0.38 each, in stock |
| 2 | Quad DAC | **MCP4728** breakout, I2C, 4 ch, 12-bit, EEPROM (e.g. Adafruit 4470) | **MCP4728-E/UN** (MSOP-10, 0.5 mm pitch - fiddly by hand, fine for machine assembly) | 1 (2 if cheap) | Opencircuit (NL) €13.00 incl. VAT, 10-12 days. AliExpress clones ~€2-4 are fine too. |
| 3 | NPN transistor, small | BC337-40 (TO-92, 800 mA) | **BC817-40** (SOT-23, 500 mA) | 10 | Q1 on a 5 V supply (≤ 0.1 W) |
| 4 | NPN transistor, medium | BD139 (TO-126, 1.5 A) | **BCP56-16** (SOT-223, 1 A); give it a generous copper pad | 6 | Q1 on 12 V (up to ~0.3 W) |
| 5 | Voltage regulator | L7805CV (TO-220, 5 V 1.5 A) | **L78M05** (DPAK, 500 mA); copper pad as heatsink | 3 | analog 5 V (XIAO shares it via D2). Not needed on a 5 V-only supply. |
| 6 | Schottky diode | 1N5819 | **SS14** (SMA, 1 A 40 V) | 5 | D1 reverse-polarity, D2 XIAO back-feed protection |
| 7 | Resistor, sense | 4.7 Ω, 1% metal film | 4.7 Ω 1%, **1206** (0.25 W) | 10 | ≤ 0.05 W, 1206 for margin |
| 8 | Resistor, sense | 5.6 Ω, 1% metal film | 5.6 Ω 1%, **1206** | 10 | |
| 9 | Resistor, sense (test) | 22 Ω, 0.25 W | - (breadboard test only) | 10 | |
| 10 | Resistor, power | **68 Ω, 2 W** | **2 × 34 Ω 1% 2512 (1 W each) in series** = 68 Ω | 6 | 12 V simple channel only. Each 2512 sees ~0.34 W. |
| 10b | Resistor, power | 47 Ω, 1 W (or 2 W) | 47 Ω **2512** (1 W) | 4 | 12 V two-op-amp version only - optional |
| 11 | Resistors, general | 100 Ω, 470 Ω, 1 k, 10 k, 100 k, 1 M - 0.25 W 1% metal film | same values, 1%, **0805** | 20 each | or an E12/E24 assortment kit |
| 12 | Potentiometer | 10 k linear, breadboard-mountable (or trimmer) | **SMD trimmer** 10 k (e.g. Bourns 3314 series) if set-and-forget; keep a **through-hole panel pot** if it's a knob people turn | 4 | bias controls (DAC takes over later) |
| 13 | Capacitor, coupling | 1 µF film (MKT/MKS), ≥ 25 V | 1 µF **X7R ceramic, 1206, 50 V** (see note) | 10 | input coupling |
| 14 | Capacitor | 150 nF film/ceramic | 150 nF X7R **0805** | 10 | DAC smoothing |
| 15 | Capacitor, ceramic | 100 pF C0G | 100 pF **C0G/NP0 0805** | 10 | op-amp compensation |
| 16 | Capacitor, ceramic | 100 nF | 100 nF X7R **0805** | 10 | decoupling |
| 17 | Electrolytic | 470 µF, ≥ 25 V | 470 µF 25 V **SMD aluminium electrolytic** (can, ~10 × 10 mm) | 3 | 12 V bulk. 16 V is enough on a 5 V-only supply. |
| 18 | Electrolytic | 100 µF, ≥ 16 V | 100 µF 16 V **SMD aluminium electrolytic** (~6.3 mm can) | 5 | bias supply filter |
| 19 | Electrolytic | 10 µF, ≥ 16 V | 10 µF X5R/X7R **1206 ceramic, 25 V** | 5 | regulator output (78xx is stable with ceramics) |
| 20 | Audio jack | 6.35 mm (1/4") stereo TRS, PCB/panel mount | keep **through-hole** - SMD 1/4" jacks are rare and weak | 4 | Tascam line outs are 1/4" TRS |
| 21 | DC jack | 5.5 × 2.1 mm barrel jack | keep **through-hole** (SMD versions exist but tear off more easily) | 2 | power in |

Notes on the SMD column:
- **Coupling cap (13):** SMD film caps exist (PPS) but are big and pricey. X7R ceramic is fine here: with 100 k after it, almost no signal voltage appears across the cap, so ceramic's voltage-dependent capacitance adds negligible distortion.
- **Power parts (4, 5, 10):** in SMD the PCB copper is the heatsink. Give SOT-223 / DPAK tabs and 2512 resistors a decent copper area (a few hundred mm², with vias to a ground or power plane on the back).
- **XIAO ESP32-S3:** has castellated pads, so it can be soldered flat onto the PCB like an SMD part, or socketed on headers (easier to swap).
- If the boards will be assembled by a service like JLCPCB, part choices shift towards their stocked "basic" parts - worth re-picking from their library at that point.

Already have (don't order): XIAO ESP32-S3, 10 mm LEDs, 12 V supply, breadboards, jumper wires.
Optional: a heatsink for TO-220/TO-126, small ferrite beads (for the 12 V line if switch-mode noise shows up).
