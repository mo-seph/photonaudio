# LEDAudioDriver - SMD parts for the PCB (2026-10-06, updated 2026-10-23 for 3.3 V analog, 2026-11-03/04 for v1)

**2026-11-04: up to 300 mA per LED, and DAC-noise fixes** (drawings: `schematics/power.png`, `channel.png`, `dac.png`; new parts in orange):
- **LED current range set per channel by R13B**, an empty footprint in parallel with R13 (see "LED current range" below). The default build stays at ≈ 95 mA.
- **R12B**, in parallel with R12, shares the heat at high current. **R11 470 → 220 Ω** for the base current.
- **Power section sized for 4 × 300 mA (1.2 A):** D1 SS14 → SS34, R24 + R24B (two 2.2 Ω 2512 in parallel), C17 1000 → 2200 µF. Supply 12 V ≥ 2 A for a high-current build.
- **DAC:** C10-C13 1 µF → 10 µF (ramp zipper noise −13 dB, measured). R16/R17 4.7k to +3V3_A → 10k to the XIAO's 3V3. New R27/R28 220 Ω in series at the XIAO's SDA/SCL.
- **C20 10 µF at each trimmer wiper**, so the trimmer bias has as little hum as the DAC bias.

**2026-11-03: v1 changes from the breadboard noise tests** (drawings: `schematics/power.png`, `schematics/channel.png`, new parts in orange on the power drawing):
- **RC filter on the analog supply:** R24 2.2 Ω + C17 1000 µF between 12V_RAW and VLED. The 12 V SMPS's burst-mode line (3.5 kHz at low LED current) came in on the rail, and a 10 Ω + 1000 µF test removed it as completely as a 9 V battery did.
- **U6 now feeds from the filtered VLED** through R25 22 Ω + C18 100 µF, not from +5V_D. That keeps the XIAO's WiFi pulses and the LED currents' audio ripple off +3V3_A, the DAC's reference. U2 now powers only the XIAO, from the unfiltered side.
- **FB1 ferrite bead** in the XIAO's 5 V feed (fit 0 Ω if it isn't needed).
- **J1 ground lift** per channel: R26 (0 Ω; 100 Ω, plus C19 10 nF, to lift the sleeve if a hum loop shows up).
- **C9 100 pF → 1 nF**, as on the breadboard (more phase margin, no audio effect).

**2026-10-23: analog side moved to 3.3 V.** U1, the bias trimmers and the DAC now run from +3V3_A (new regulator U6). The level shifter is gone, R9 is 1.6k, R14 is 470k, and LED_SUPPLY_SEL is removed. U2 (7805) stays only to power the XIAO.

Designators match `schematics/LED Driver.sch` (2026-10-06 SMD version) plus the new U6, C15, C16 (2026-10-23), R24-R26, C17-C19, FB1 (2026-11-03) and R12B, R13B, R24B, R27, R28, C20 (2026-11-04; use R29-R32 instead of the "B" names if Fusion wants plain numbers). Your schematic uses 1206 for most passives - that's fine too; 0805 is just smaller.
Board = power section once + DAC section once + **4 × channel**. "Total" counts the whole board.

Sizes: passives **0805** unless noted (2026-10-06: everything except C1/C4 can be 0805) (comfortable to hand-solder). The only fiddly part is U5, the DAC (MSOP-10, 0.5 mm pitch). Connectors and the power jack stay through-hole for strength.

## Power section (once)

| Ref | Value | SMD part / package | Total | Notes |
|---|---|---|---|---|
| D1 | Schottky **3 A** 40 V | **B340A** (Diodes Inc. B340A-13-F), **SMA**, the same footprint as D2: SparkFun-DiscreteSemi DIODE-SCHOTTKY, device "-B340A" (2026-11-06; was SS34-E3/57T in SMC). Order by full part number: "SS34" covers SMA, SMB and SMC parts | 1 | reverse-polarity protection. Was SS14; sized for 1.2 A of LEDs (≈ 0.5 V, 0.6 W at 1.2 A) |
| D2 | Schottky 1 A 40 V | SS14 (SMA) | 1 | XIAO back-feed protection |
| U2 (VR2 in Fusion) | 5 V regulator | **LD1117S50** (SOT-223) - Dave's choice in 'LED Power and Digital' (2026-11-05); was L78M05ACDT | 1 | fed from 12V_RAW (before R24); powers only the XIAO (via FB1, D2). **Tab = OUT (5 V), not GND:** the heatsink copper sits on the 5 V net, not the ground pour. ≈ 6.6 V × I_XIAO: ≈ 0.3-0.4 W without WiFi; give the tab ~1-2 cm² of copper. Needs ≥ 10 µF with some ESR at its output (C3) |
| FB1 | ferrite bead (new v1) | 0805, ≈ 600 Ω at 100 MHz, **≥ 1 A**, DCR ≤ 0.2 Ω | 1 | between +5V_D and D2: keeps the XIAO's RF off U2's output. Fit a 0 Ω link instead if not needed |
| R24, R24B | 2.2 Ω (new v1) | **2512, 1 W** | 2 | in parallel (1.1 Ω), 12V_RAW → VLED; **fit both**. Drops 0.44 V at 400 mA (4 × 100 mA); 1.3 V and 0.8 W in each at 1.2 A (4 × 300 mA) |
| C17 | **2200 µF 25 V** (new v1) | **low-ESR** aluminium electrolytic (≤ 0.03 Ω at 100 kHz, ripple ≥ 1.5 A): radial 12.5-16 mm through-hole (e.g. Panasonic FR / FM series) or a 16 mm SMD can | 1 | VLED to GND. With R24 ∥ R24B: corner 66 Hz, ≈ −34 dB at 3.5 kHz. A general-purpose can's ESR limits that to ≈ −25 dB. − leg to the power-entry ground, next to C1 |
| R25 | 22 Ω (new v1) | 0805 1% | 1 | VLED → U6 input |
| C18 | 100 µF 25 V (new v1) | SMD aluminium electrolytic, ~6.3 mm | 1 | at U6's input, after R25 (corner 72 Hz). Sees ~11 V, so 25 V rating |
| U6 | 3.3 V regulator | **LD1117S33** (SOT-223), or LD1117V33 / LD33CV in TO-220 for the breadboard | 1 | analog rail +3V3_A, **fed from VLED via R25 / C18** (v1; was +5V_D). ≈ 0.1 W at ~11 V in, ~10 mA. Max input 15 V, so 12 V supplies only. **Pinout GND, OUT, IN - not like a 7805.** Tab = OUT |
| C15 | 100 nF | X7R 0805, **50 V** | 1 | at U6's input pin (now sees ~11 V) |
| C16 | 10 µF 10 V | tantalum, 3216 (case A) or 3528 (case B) | 1 | at U6's output - the LD1117 needs ≥ 10 µF with some ESR (≳ 0.25 Ω, per ST's forum; the datasheet doesn't say) to stay stable. 'LED Power and Digital' has a 1206 ceramic here: swap the footprint |
| C1 | 470 µF 25 V | SMD aluminium electrolytic, ~10 × 10 mm | 1 | bulk at the power entry (12V_RAW), before R24 |
| C2 | 330 nF | X7R 0805, 50 V | 1 | ceramic right at U2's IN pin. C1 provides the bulk. |
| C3 | 10 µF 16 V | **tantalum, 3216 (case A) or 3528 (case B)** | 1 | U2's output. Now that U2 is an LD1117, the same applies as for C16: a plain ceramic is not a safe bet (ST suggest ESR ≳ 0.25 Ω). Or use a ceramic with a 1 Ω 0805 in series |
| R1 | 100 Ω | 0805 1% | 1 | |
| C4 | 100 µF 16 V | SMD aluminium electrolytic, ~6.3 mm | 1 | bias supply filter (now +3V3_BIAS) |
| ~~LED_SUPPLY_SEL~~ | removed 2026-10-23 | | 0 | with no 5 V analog rail, the LEDs always run from VLED (12 V) |
| J3 | power input | PJ-102AH DC jack (2.0 mm pin - fits 5.5 × 2.1 mm plugs), through-hole | 1 | pin 1 = centre (+12), pin 2 = sleeve (GND), pin 3 = switch (unused). Check its current rating covers ≈ 1.5 A for a 4 × 300 mA build |

## Per channel (× 4)

| Ref | Value | SMD part / package | Total | Notes |
|---|---|---|---|---|
| U1 | dual op-amp | **MCP6002-I/SN** (SOIC-8) | 4 | runs from +3V3_A. Must be rail-to-rail: an LM358 can't work on 3.3 V |
| C14 | 100 nF | X7R 0805 | 4 | right next to U1 pin 8 (was C1000) |
| J1 (AUDIO_IN in Fusion) | 3.5 mm stereo jack, 2 break contacts | **Lumberg 1503 09** (through-hole, 1 A 34 V) | 4 | **pins 1 = sleeve, 2 = tip, 3 = ring, 4 = tip break, 5 = ring break** (datasheet contact diagram; confirmed by Dave 2026-11-05 - an earlier note here had 2/3 and 4/5 swapped). The Ultra Librarian symbol had tip and ring swapped (drawn the other way up); Dave renumbered it to the datasheet. Pad numbers follow the datasheet layout. Tip (2) → C8 / + input, ring (3) → C7 / − input. **1, 4, 5 → the SLEEVE net**, so an unplugged input is shorted and silent. SLEEVE → R26 (R_LIFT) → GND at the power entry. Insulate the metal bush from a metal panel, so the panel doesn't bypass the ground lifts. **Footprint:** the Ultra Librarian part has the right pin positions, but it fakes each slot with two overlapping zero-ring drills, an SMD pad and a Dimension-layer line, which gives about 200 DRC errors. Rebuild it with Fusion's slotted PTH pads (0.9 × 1.6 mm slots, 1.7 × 2.4 mm copper): `schematics/jack_1503_09_footprint.png` |
| J_LED | 3.5 mm jack | **Lumberg 1503 09** | 4 | replaces the 2-pin LED header (2026-11-05). Tip (2) = LED anode (from R12 / R12B), sleeve (1) = cathode (U3 collector). Ring (3): unconnected, or tied to sleeve so TRS-wired LED cables work. **4, 5 unconnected** (4 touches the tip with no plug). **The sleeve is not ground:** keep it off any metal panel, or the LED loses its current limit. Label it clearly: an audio cable plugged in by mistake gets 12 V through R12 |
| R26 (R_LIFT) | 0 Ω (new v1), or 100 Ω with a jumper | 0805 | 4 | J1 sleeve ground lift, placed at its jack and joined to the main plane there (2026-11-06; was at the power-entry star - see the layout notes). Switchable option: fit 100 Ω + C19 permanently with a 2-pin jumper (or a gold-contact DIP, e.g. one 4-way for all channels) across R26: on = bonded, off = lifted. Only shield / leakage current flows here, so contact resistance doesn't matter |
| C19 | 10 nF (new v1) | X7R 0805 50 V; **not fitted** with a 0 Ω R26 | 4 | across R26: keeps the shield RF-grounded when lifted |
| R_KEL | 0 Ω (new v1) | 0805 | 4 | ties the channel's K_GND (LED return / Kelvin net) to GND, **at the star (C17's −)**, not in the channel area |
| C7, C8 | 1 µF | X7R 0805 25 V (1206 50 V keeps more of its value under DC) | 8 | they sit at a few volts DC; even at ~half value the low-frequency corner is only ~3 Hz |
| R2, R3 | 1 MΩ | 0805 1% | 8 | |
| R4, R5, R6, R7 | 100 kΩ | 0805, **0.1% thin film** recommended (1% works) | 16 | how well these match sets the hum rejection: 1% → ~35 dB, 0.1% → ~55 dB |
| R8 | 10 kΩ | 0805 1% | 4 | |
| R9 | **1.6 kΩ** | 0805 1% (E24) | 4 | was 1k on 5 V. 3.3 V × 1.6/11.6 = 0.455 V → ~95 mA full scale. With only E12 values, 1.5k gives ~91 mA |
| C9 | **1 nF** | C0G/NP0 0805 | 4 | was 100 pF; 1 nF on the breadboard since 2026-11-02 (more phase margin, no audio effect) |
| R10 | 1 kΩ | 0805 1% | 4 | |
| R11 | **220 Ω** | 0805 1% | 4 | was 470 Ω: leaves the op-amp enough drive for U3's base current up to 300 mA (≈ 3-6 mA). Harmless at 100 mA |
| U3 | NPN | **BCP56-16** (SOT-223) | 4 | tab (pad 4, "EPAD") is the collector: connect it to the collector net and give it copper - **not** ground. Pins 1 = B, 2 = C, 3 = E. Give each tab ≥ 2 cm² of copper (top + bottom island with vias): it peaks at ≈ 0.8 W in a 300 mA build. Its gain falls off at high current; for 300 mA consider a higher-gain part with the same pinout (BCP68-25 is one to check: hFE at 300 mA, VCEO ≥ 15 V) |
| R12 | 47 Ω | **2512, 1 W** | 4 | ~0.47 W at 100 mA. For other currents / LEDs see "LED current range" |
| R12B | not fitted (new v1) | **2512, 1 W** | 4 | in parallel with R12, to share the heat. 300 mA build: R12 = R12B = 33 Ω (≈ 0.75 W each) |
| R13 | 4.7 Ω | 1206 1%, ≤ 100 ppm/°C | 4 | current sense: I_FS = 0.455 V / (R13 ∥ R13B) |
| R13B | not fitted (new v1) | 1206 1%, ≤ 100 ppm/°C | 4 | **sets the range**, in parallel with R13: none ≈ 97 mA, 10 Ω ≈ 142, 4.7 Ω ≈ 194, 3.3 Ω ≈ 235, 2.2 Ω ≈ 303 mA |
| C20 | 10 µF (new v1) | X5R/X7R 1206 16 V (0805 works) | 4 | trimmer wiper (BIAS_SEL pin 3) to GND: the wiper's ~2.5k source impedance otherwise unbalances U1A (R7 path) and lets in hum (+15 dB at 50 Hz measured with the trimmer) |
| R14 | **470 kΩ** | 0805 | 4 | +3V3_A → U1 pin 6: ~7 mV offset so a zero command is fully off (added 2026-10-10 as 1M on 5 V; 470k on 3.3 V to beat the MCP6002's 4.5 mV worst-case offset) |
| R15 | 10 k trimmer | **Bourns 3314J-1-103E** (the schematic uses the RTRIM3314J footprint) | 4 | |
| ~~LED~~ | replaced by J_LED (2026-11-05) | | 0 | |
| BIAS_SEL | bias select | 1×3 2.54 mm header + jumper | 4 | 1 = DAC, 2 = Vbias, 3 = trimmer. A 3-way choice: keep the header (a DIP can't do it; a changeover / SPDT slide switch could) |
| JP2, JP1 (were JP4, JP5) | DC-coupling links (optional) | 1×2 header, across C8 / C7 | 8 | in the audio path: if these become DIP switches, use gold contacts |

## DAC section (once)

| Ref | Value | SMD part / package | Total | Notes |
|---|---|---|---|---|
| U5 | quad 12-bit DAC | **MCP4728-E/UN** (MSOP-10) | 1 | address 0x60, VDD reference set in firmware (the internal 2.048 V also works: finer steps, bias tops out at 62% of full scale) |
| C5 | 100 nF | X7R 0805 | 1 | at U5 pin 1 |
| C6 | 10 µF | X5R 0805 16 V | 1 | |
| ~~Q2, Q3, R18, R19~~ | removed 2026-10-23 | | 0 | no level shifter: the DAC now runs at 3.3 V like the XIAO |
| R16, R17 | **10 kΩ** | 0805 | 2 | I2C pull-ups **to the XIAO's 3V3** (was 4.7k to +3V3_A), so their current stays off the analog rail (R17 = SDA, R16 = SCL) |
| R27, R28 | 220 Ω (new v1) | 0805 | 2 | in series at the XIAO's SDA (R27) / SCL (R28) pins, before the pull-ups: softens the edges |
| R20-R23 | 1 kΩ | 0805 1% | 4 | DAC smoothing. Keep at 1k: it adds to R7 and would unbalance U1A |
| C10-C13 | **10 µF** | X5R/X7R 1206 16 V (0805 works) | 4 | DAC smoothing, 16 Hz (was 1 µF, 160 Hz): ramp zipper noise −13 dB measured. Bias changes settle in ~10 ms |
| U4 | XIAO ESP32-S3 | Seeed hybrid footprint: solder flat by the castellations, or on headers | 1 | |
| J2 (I2C in Fusion) | network I2C | Qwiic: JST SH 4-pin right-angle, SM04B-SRSS-TB | 1 | pin 1 GND (via the I2C_GND 0 Ω, which can be swapped for a lift), 2 = 3.3 V not connected (data only), 3 SDA_NET, 4 SCL_NET |

## Order list (TME), 2026-11-05

Sizes and designators follow the Fusion exports of 2026-11-05 18:05 ('Driver Channel.sch', 'LED Power and Digital.sch'). Where the two differ, this list follows the schematic rather than the 0805 defaults in the tables above.
- **Board** is the count for one board. **Order** is a suggestion for one board plus spares, rounded up to typical minimum quantities.
- **The part numbers are suggestions, not checked against TME's stock.** TME's site blocks my browser, so none of these links have been opened.
  - Each link is a TME search for the part number. If one comes up empty, any part with the same value, package and rating will do.
  - Check the can size for C1, C4 / C18 and C17 before ordering: they have to match their footprints.
- **Dave's TME cart (2026-11-06), checked against this list:** every resistor, capacitor and semiconductor is there, in the right value, package and rating. Dave already has the XIAO, DC jacks, 3.5 mm jacks, headers and jumpers.
  - Substitutes in the cart, all OK:
    - Viking AR06BTCV1003 (100k 0.1%)
    - Walsin WR12X1601FTL (1.6k)
    - Royal Ohm 1206S4J0102T5E (1k 5%)
    - Vishay CRCW25122R20JNTHBC (2.2 Ω 2512 5%; needs ≥ 1 W)
    - Yageo CC0805KKX7R9BB334 (330 nF) and CC0805KRX7R9BB103 (10 nF)
    - KEMET C0805C102J5GAC (1 nF C0G)
    - Taiyo Yuden EMK212ABJ106KG-T (10 µF 0805)
    - EEU-FR1E222S for C17
  - Not in the cart: the Qwiic connector J2 (SM04B-SRSS-TB).
  - MCP6002-I/SN wasn't in stock: TME quoted 2 weeks.

**Resistors** (1% thick film unless noted)

| Value | Package | Refs | Board | Order | Suggested part | TME |
|---|---|---|---|---|---|---|
| 1 MΩ | 1206 | R2, R3 | 8 | 10 | Yageo RC1206FR-071ML | [search](https://www.tme.eu/gb/en/katalog/?queryPhrase=RC1206FR-071ML) |
| 100 kΩ **0.1%** thin film | 1206 | R4-R7 | 16 | 20 | Yageo RT1206BRD07100KL | [search](https://www.tme.eu/gb/en/katalog/?queryPhrase=RT1206BRD07100KL) |
| 470 kΩ | 1206 | R14 | 4 | 10 | Yageo RC1206FR-07470KL | [search](https://www.tme.eu/gb/en/katalog/?queryPhrase=RC1206FR-07470KL) |
| 10 kΩ | 1206 | R8, R16, R17 | 6 | 10 | Yageo RC1206FR-0710KL | [search](https://www.tme.eu/gb/en/katalog/?queryPhrase=RC1206FR-0710KL) |
| 1.6 kΩ | 1206 | R9 | 4 | 10 | Yageo RC1206FR-071K6L | [search](https://www.tme.eu/gb/en/katalog/?queryPhrase=RC1206FR-071K6L) |
| 1 kΩ | 1206 | R10, R20-R23 | 8 | 10 | Yageo RC1206FR-071KL | [search](https://www.tme.eu/gb/en/katalog/?queryPhrase=RC1206FR-071KL) |
| 220 Ω | 1206 | R11, R27, R28 | 6 | 10 | Yageo RC1206FR-07220RL | [search](https://www.tme.eu/gb/en/katalog/?queryPhrase=RC1206FR-07220RL) |
| 100 Ω | 1206 | R1 | 1 | 10 | Yageo RC1206FR-07100RL | [search](https://www.tme.eu/gb/en/katalog/?queryPhrase=RC1206FR-07100RL) |
| 4.7 Ω | 1206 | R13 (+ R13B for the 194 mA range) | 4 | 10 | Yageo RC1206FR-074R7L | [search](https://www.tme.eu/gb/en/katalog/?queryPhrase=RC1206FR-074R7L) |
| 22 Ω | 0805 | R25 | 1 | 10 | Yageo RC0805FR-0722RL | [search](https://www.tme.eu/gb/en/katalog/?queryPhrase=RC0805FR-0722RL) |
| 0 Ω | 0805 | R_KEL, R_LIFT, I2C_GND | 9 | 20 | Yageo RC0805JR-070RL | [search](https://www.tme.eu/gb/en/katalog/?queryPhrase=RC0805JR-070RL) |
| 100 Ω | 0805 | R_LIFT for the J_LIFT option (instead of 0 Ω) | (4) | 10 | Yageo RC0805FR-07100RL | [search](https://www.tme.eu/gb/en/katalog/?queryPhrase=RC0805FR-07100RL) |
| 47 Ω 1 W | 2512 | R12 (+ R12B for the 194 mA range) | 4 | 10 | Yageo RC2512FK-0747RL | [search](https://www.tme.eu/gb/en/katalog/?queryPhrase=RC2512FK-0747RL) |
| 2.2 Ω 1 W | 2512 | R24, R24B | 2 | 5 | Yageo RC2512FK-072R2L | [search](https://www.tme.eu/gb/en/katalog/?queryPhrase=RC2512FK-072R2L) |
| *300 mA build only:* 33 Ω 1 W | 2512 | R12 + R12B | (8) | - | Yageo RC2512FK-0733RL | [search](https://www.tme.eu/gb/en/katalog/?queryPhrase=RC2512FK-0733RL) |
| *300 mA build only:* 2.2 Ω | 1206 | R13B | (4) | - | Yageo RC1206FR-072R2L | [search](https://www.tme.eu/gb/en/katalog/?queryPhrase=RC1206FR-072R2L) |

**Capacitors**

| Value | Package | Refs | Board | Order | Suggested part | TME |
|---|---|---|---|---|---|---|
| 100 nF 50 V X7R | 0805 | C14, C5, C15 | 6 | 20 | Samsung CL21B104KBCNNNC | [search](https://www.tme.eu/gb/en/katalog/?queryPhrase=CL21B104KBCNNNC) |
| 330 nF 50 V X7R | 0805 | C2 | 1 | 10 | Samsung CL21B334KBFNNNE | [search](https://www.tme.eu/gb/en/katalog/?queryPhrase=CL21B334KBFNNNE) |
| 1 µF 25 V X7R | 0805 | C7, C8 | 8 | 20 | Samsung CL21B105KAFNNNE | [search](https://www.tme.eu/gb/en/katalog/?queryPhrase=CL21B105KAFNNNE) |
| 1 nF 50 V C0G | 0805 | C9 | 4 | 10 | Samsung CL21C102JBANNNC | [search](https://www.tme.eu/gb/en/katalog/?queryPhrase=CL21C102JBANNNC) |
| 10 nF 50 V X7R | 0805 | C19 (only for the J_LIFT option) | (4) | 10 | Samsung CL21B103KBANNNC | [search](https://www.tme.eu/gb/en/katalog/?queryPhrase=CL21B103KBANNNC) |
| 10 µF 16 V X5R | 0805 | C20 | 4 | 10 | Samsung CL21A106KOQNNNE | [search](https://www.tme.eu/gb/en/katalog/?queryPhrase=CL21A106KOQNNNE) |
| 10 µF 16 V X7R | 1206 | C6, C10-C13 | 5 | 10 | Samsung CL31B106KOHNNNE | [search](https://www.tme.eu/gb/en/katalog/?queryPhrase=CL31B106KOHNNNE) |
| 10 µF 16 V tantalum | case A (3216-18) | C3, C16 | 2 | 5 | AVX TAJA106K016RNJ | [search](https://www.tme.eu/gb/en/katalog/?queryPhrase=TAJA106K016RNJ) |
| 100 µF 25 V electrolytic | SMD can **6.3 mm Ø** (153CLV-0605) | C4, C18 | 2 | 5 | Panasonic EEE-FK1E101P (6.3 × 7.7) | [search](https://www.tme.eu/gb/en/katalog/?queryPhrase=EEE-FK1E101P) |
| 470 µF 25 V electrolytic | SMD can **10 mm Ø** (ECAP-10.5MM) | C1 | 1 | 2 | Panasonic EEE-FK1E471P (10 × 10.2) | [search](https://www.tme.eu/gb/en/katalog/?queryPhrase=EEE-FK1E471P) |
| 2200 µF 25 V **low-ESR** | radial **16 mm Ø, 7.5 mm pitch** (E7,5-16) | C17 | 1 | 2 | Panasonic **EEU-FR1E222S**: 16 × 20 mm, 7.5 mm pitch (distributor listings), so it fits E7,5-16 | [search](https://www.tme.eu/gb/en/katalog/?queryPhrase=EEU-FR1E222S) |

**Semiconductors**

| Part | Package | Refs | Board | Order | Suggested part | TME |
|---|---|---|---|---|---|---|
| dual op-amp | SOIC-8 | U1 | 4 | 5 | Microchip MCP6002-I/SN | [search](https://www.tme.eu/gb/en/katalog/?queryPhrase=MCP6002-I%2FSN) |
| quad 12-bit DAC | MSOP-10 | U5 | 1 | 2 | Microchip MCP4728-E/UN | [search](https://www.tme.eu/gb/en/katalog/?queryPhrase=MCP4728-E%2FUN) |
| NPN 1 A | SOT-223 | U3 | 4 | 5 | onsemi BCP56-16T1G (or Nexperia BCP56-16,115) | [search](https://www.tme.eu/gb/en/katalog/?queryPhrase=BCP56-16) |
| 3.3 V LDO | SOT-223 | VR1 (U6) | 1 | 2 | ST LD1117S33TR | [search](https://www.tme.eu/gb/en/katalog/?queryPhrase=LD1117S33TR) |
| 5 V LDO | SOT-223 | VR2 (U2) | 1 | 2 | ST LD1117S50TR | [search](https://www.tme.eu/gb/en/katalog/?queryPhrase=LD1117S50TR) |
| Schottky 3 A 40 V | SMA (DO-214AC) | D1 | 1 | 2 | Diodes Inc. B340A-13-F, or any 3 A 40 V Schottky listed as SMA / DO-214AC | [search](https://www.tme.eu/gb/en/katalog/?queryPhrase=B340A-13-F) |
| Schottky 1 A 40 V | SMA (DO-214AC) | D2 | 1 | 5 | Vishay SS14-E3/61T | [search](https://www.tme.eu/gb/en/katalog/?queryPhrase=SS14-E3%2F61T) |
| ferrite bead, 220-600 Ω @ 100 MHz, ≥ 0.5 A | 0805 | FB1 | 1 | 5 | Murata BLM21PG331SN1D (330 Ω, 1.5 A) | [search](https://www.tme.eu/gb/en/katalog/?queryPhrase=BLM21PG331SN1D) |

**Connectors, trimmers, module**

| Part | Refs | Board | Order | Suggested part | TME |
|---|---|---|---|---|---|
| 3.5 mm stereo jack, 2 breaks | AUDIO_IN, J_LED | 8 | 8 | Lumberg 1503 09 | [search](https://www.tme.eu/gb/en/katalog/?queryPhrase=1503%2009) |
| DC jack 2.0 mm pin | PWR_IN (J3) | 1 | 2 | Same Sky (CUI) PJ-102AH | [search](https://www.tme.eu/gb/en/katalog/?queryPhrase=PJ-102AH) |
| 10 k trimmer, top adjust | R15 | 4 | 5 | Bourns 3314J-1-103E | [search](https://www.tme.eu/gb/en/katalog/?queryPhrase=3314J-1-103E) |
| JST SH 4-pin right-angle (Qwiic) | I2C (J2) | 1 | 2 | JST SM04B-SRSS-TB | [search](https://www.tme.eu/gb/en/katalog/?queryPhrase=SM04B-SRSS-TB) |
| 2.54 mm pin header, 1×40 break-away | BIAS_SEL (1×3 ×4), J_DC_HOT / J_DC_COLD (1×2 ×8), J_LIFT (1×2 ×4) | 28 pins | 1 strip | any | [search](https://www.tme.eu/gb/en/katalog/?queryPhrase=pin%20header%202.54%201x40) |
| 2.54 mm jumper (shunt) | the above | 16 | 20 | any; gold-plated for J_DC_* (audio path) | [search](https://www.tme.eu/gb/en/katalog/?queryPhrase=jumper%202.54) |
| XIAO socket (2026-11-06) | U4 | 2 | 4 | 1×7 female header, 2.54 mm, straight THT, ~8.5 mm high, e.g. Connfly ZL262-7SG. Not checked against TME. A 1×20 strip cut to length works too, but each cut wastes a contact | [search](https://www.tme.eu/gb/en/katalog/?queryPhrase=ZL262-7SG) |
| XIAO ESP32-S3 | U4 | 1 | 1 | Seeed 113991114 (skip if you have one) | [search](https://www.tme.eu/gb/en/katalog/?queryPhrase=113991114) |

## LED current range (per channel, 2026-11-04)

Full scale I_FS = 0.455 V / (R13 ∥ R13B). Fit R13B to change the range; nothing has to be removed.

| R13B | R13 ∥ R13B | Full scale | R12 (+ R12B) for a ~3.7 V white LED | U3 peak |
|---|---|---|---|---|
| not fitted | 4.7 Ω | ≈ 97 mA | 47 Ω, R12B not fitted | ≈ 0.3 W |
| 4.7 Ω | 2.35 Ω | ≈ 194 mA | 2 × 47 Ω (23.5 Ω) | ≈ 0.5 W |
| 2.2 Ω | 1.50 Ω | ≈ 303 mA | 2 × 33 Ω (16.5 Ω) | ≈ 0.8 W |

- **R12 total** ≈ (VLED − Vf − 0.45 V − 1 V) / I_FS. VLED ≈ 10.2 V with all four channels at 300 mA, ≈ 11 V otherwise; the 1 V keeps U3 out of saturation. Lower-Vf LEDs (IR, red) can take more R12, which keeps U3 cooler.
- **Heat at 300 mA:** ≈ 2.3 W per channel (R12 pair ≈ 1.5 W, U3 ≈ 0.65-0.8 W, R13 0.14 W). Four channels at full brightness ≈ 11 W including R24/D1, so leave room and airflow around R12 / U3. With audio around mid-bias the average is about half.
- **The noise and resolution stay the same relative to full scale** (1 LSB = 1/4096 of I_FS; ground sensitivity 1/R13 per mV, the same fraction of I_FS).
- **Before a 300 mA build:** check the LED's ratings and its heatsinking. Check U3's gain at 300 mA (or fit the higher-gain part). Check the supply (12 V, ≥ 2 A).
- **No trimmer for the range:** it would sit in the signal divider, adding noise and drift, and could over-drive an LED by accident.
- **Changing R13 itself works just as well**: R13B only saves desoldering. Examples: 22 Ω ≈ 21 mA, 10 Ω ≈ 46 mA, 4.7 Ω ≈ 97 mA, 1.5 Ω ≈ 303 mA.
  - For range jumpers (several R13B values switched in parallel), use **solder jumpers, not header shunts**. The jumper sits in the current-sense path, so a loose shunt's contact resistance would modulate the LED current.
- **R12 only limits the top:** with R12 = 47 Ω the current tops out at ≈ 130 mA (white LED), whatever R13 asks for. U3 then saturates and the peaks clip, but nothing is harmed. Below that, 47 Ω is fine all the way down (20 mA: U3 ≈ 0.13 W).
- **A part-fitted power section** (R24 alone, without R24B; or SS14 for D1; or 1000 µF for C17) still works; it just limits the board total. R24 alone (1 W) allows ≈ 0.5 A in total; an SS14 allows 1 A. Lay out the full-size footprints either way.

## Layout notes for v1 (2026-11-03/04)

- One unbroken ground plane on the bottom layer.
- Power entry: J3 GND and C1's and C17's − legs meet at one point (the star), so the caps' ripple currents go straight back to the supply. The LRTN links join there.
- **J1 sleeves (2026-11-06):** ground each one to the main plane at its own jack, with R26 / J_LIFT / C19 beside the jack. A trace back to the star isn't needed.
  - The sleeve carries charger / interface leakage, ≲ 0.25 mA. On 1 oz copper (≈ 0.5 mΩ per square) that drops < 1 µV, about 1/1000 of a DAC step.
  - Use the main plane only: not the XIAO island and not an LRTN net.
  - The "At star point" note by R_LIFT on the channel sheet no longer applies; the one by R_KEL still does.
  - J_LED sleeves are the LED cathode (U3 collector), not ground. Keep pours off them.
- **XIAO ground island (Dave's layout, 2026-11-06):** fine, joined to the main plane at one link.
  - **U5 (DAC), C5/C6 and C10-C13 go on the main plane**, not the island. The DAC's output is the bias for all four channels, so it must share their ground. Ground noise between the bias ground and the star reaches R13 through R8/R9: 1 mV ≈ one DAC step. On the island, the XIAO's supply current (tens of mA, ~350 mA WiFi bursts) times the link's few mΩ would put about that much on all four biases at once.
  - **Every trace between the island and the rest crosses at the link:** SDA_DAC / SCL_DAC (so the I2C return current runs under them) and the 5 V feed (FB1 / D2). Put U5 right beside the link.
  - Put the link on the side facing J3, so the XIAO's return current reaches the star without crossing the channels.
  - J2 (Qwiic) goes on the island side, so the network I2C lines don't cross the gap.
  - Above R20/C10's 16 Hz corner, each bias follows the ground of its C10-C13 cap. Grounding those caps towards their own channel helps a little, if it's easy.
- Keep U2 / XIAO return currents (WiFi bursts up to ~350 mA) away from U1 pin 4 and R13's ground. Any millivolt between U1's ground and R13's bottom becomes LED current (0.21 mA per mV with R13 = 4.7 Ω, 0.67 mA with 1.5 Ω).
- **Kelvin connection at R13:** take U1's ground (pin 4, R9, C14) from R13's bottom pad, and route the LED return from that pad to the power entry on its own. R10 picks up R13's top at the pad, not along the emitter trace. Keep each LED current loop (VLED → R12 → LED → U3 → R13) compact.
  - **In Fusion:** give each channel its own return net, LRTN_A to LRTN_D: R13/R13B bottom pads, R9's bottom, U1 pin 4, C14. Join it to GND at the star (C17's − pad, beside J3 GND and C1's −) through a 0 Ω link (0805 per channel, or one 1206 for all four) or a net-tie footprint. Then the GND pour stays off it, and the LED current stays in its own trace.
  - **Join the four returns only at the star.** A shared stretch carries the other channels' current, which shows up as crosstalk: a 10 mm × 1.5 mm shared trace at 4 × 300 mA gives ≈ −60 dB with the Kelvin R9, ≈ −44 dB without.
  - LED_SUPPLY / VLED feeds can share a trunk; the current sink ignores small supply drops.
- **Current:** LED path traces ≥ 0.6 mm (300 mA). The VLED trunk, R24/R24B, D1 and the ground returns ≥ 1.5 mm or pours (1.2 A).
- **Heat:** copper islands on each U3 tab (collector net, not ground) and around R12/R12B; space the four channels apart.
- C15/C16 within ~1 cm of U6's pins, C2/C3 of U2's, C14 at each U1 pin 8, C5/C6 at U5's pins.
- **I2C (XIAO ↔ DAC):** short traces over unbroken ground (crossing at the island's link), away from J1, U1A's inputs, Vbias / BIAS_SEL and R13. Keep the XIAO and U5 ground returns local. R27/R28 at the XIAO pins. Every DAC write adds a click, so firmware should write only when the value changes (500 writes/s measured as a 500 Hz comb at −83 dB re signal).
- **USB:** the XIAO on USB makes a ground loop through the computer (measured as extra hum). Run it off USB in use, and use a plug-in USB isolator for development.
