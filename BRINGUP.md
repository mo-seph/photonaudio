# LEDAudioDriver - breadboard bring-up (2026-10-06; 3.3 V overrides 2026-10-23)

Step-by-step build and test of **one channel + power + XIAO + DAC**, in an order where each stage is tested before the next depends on it. Designators match `schematics/LED Driver.sch` and the drawings in `schematics/` (`power.png`, `channel.png`, `dac.png`).

Fill in the "Measured" columns as you go - they're the record of what the hardware actually does.

## ⚡ 3.3 V rebuild (2026-10-23) - read this first
The analog side now runs from **3.3 V** (see the updated `power.png`, `channel.png`, `dac.png`). The stages below were written for the 5 V version. Follow them, but **these values override theirs**:

| What | 3.3 V version |
|---|---|
| Regulator | **LD33CV / LD1117V33** (TO-220) from 12 V, in place of the 7805 (XIAO on USB). **Pinout differs from a 7805: legs are GND, OUT, IN** (check your part's datasheet). 100 nF on its input (C15), **≥ 10 µF electrolytic/tantalum on its output (C16)** - it needs that to stay stable |
| Rails | **+3V3_A** = 3.25-3.35 V (feeds U1 pin 8, R14, the DAC); **+3V3_BIAS** via R1/C4 (feeds the trimmer) |
| U1 | **MCP6002 only** - an LM358 doesn't work on 3.3 V. C14 = 100 nF across pins 8/4 |
| R9 | **1.6k** (or 1.5k if that's what you have: ~91 mA max) |
| R14 | **470k** from +3V3_A to pin 6 (~7 mV offset) |
| C9 | 100 pF (now you have the right caps) |
| C7, C8 | 1 µF (or keep the wire links for DC coupling) |
| LED_SUPPLY_SEL | **gone** - R12 goes straight to the 12 V rail |
| Safe first power-up (replaces the old "5 V position") | fit **470 Ω** as R12 for stage 2a: the LED can't exceed ~18 mA whatever's miswired. Swap in 47/68 Ω for stage 2b |
| Pin 5 at full | **≈ 0.455 V** (wiper ÷ 7.25) |
| V(R13) at full | ≈ 0.45 V → **~95 mA** |
| Stage 3: V1 range | 0-3.3 V |
| Stage 4: full audio swing | **±1.65 V peak** around mid bias (~+3.4 dBu) - turn the Tascam down a bit |
| Stage 7: DAC | breakout **VCC → +3V3_A**, SDA/SCL **straight to the XIAO** - no level shifter. The breakout's own pull-ups are then at 3.3 V, which is safe |

## 0. Before you start

### Breadboard stand-ins for the SMD parts

| Schematic | PCB part | Breadboard part | Pins (breadboard part) |
|---|---|---|---|
| U1 | MCP6002-I/SN | **MCP6002-I/P** or **LM358** (DIP-8) | 1 OUT A, 2 −IN A, 3 +IN A, 4 GND, 5 +IN B, 6 −IN B, 7 OUT B, 8 +5V. Notch/dot = pin 1 end |
| U2 | L78M05 DPAK | **L7805CV** (TO-220) | text facing you, legs down: IN, GND, OUT |
| U3 | BCP56-16 | **BC337** (TO-92, best of the small ones), or BD139 (TO-126). Also OK: S8050, 2N2222 (TO-92). At a pinch: 2N3904, C1815 (weak at 100 mA). Must be NPN | BC337: flat face towards you, legs down: C, B, E. BD139: text facing you: E, C, B. **Other TO-92 parts differ** (2N3904/S8050: E, B, C; C1815: E, C, B; 2N2222 varies by maker) - check the datasheet for your exact part |
| D1, D2 | SS14 | **1N5819** | band = cathode |
| R12 | 47 Ω 2512 | 47 Ω **≥ 1 W**, or **68 Ω 2 W with a TO-92 transistor** (it cuts the transistor's worst case from ~0.3 W to ~0.22 W, and still leaves ~0.6 V headroom at full current on 12 V with this LED's measured 3.95 V - tight but workable) | dissipates up to ~0.45-0.65 W - a ¼ W resistor will cook |
| R15 | 3304W trimmer | 10k pot | ends to +5V_BIAS and GND, wiper to BIAS_SEL pin 3 |
| LED connector | 2-pin header | the 10 mm LED itself | long leg (anode) to R12 |
| J1 | 1/4" TRS jack | jack breakout, or a TRS lead with clips | tip, ring, sleeve |
| U5 + Q2/Q3 + R16-R19 | MCP4728 + BSS138 shifter | MCP4728 breakout (Adafruit 4470) + a **BSS138 level-shifter module** | see stage 7 |

**Keep R9 = 1k on the breadboard, even with an LM358.** (An earlier note said 1.5k for the LM358; that's withdrawn. 1.5k would let stage 2 drive the LED to ~140 mA when it is fed straight from the trimmer.) With an LM358, max LED current is then ~68 mA, because its output stops at ~3.5 V. That's fine for testing; the MCP6002 gives the full ~97 mA.

### Safety rules
- Power off while wiring. Check LED and electrolytic polarity before powering.
- If you have a bench supply, use it for stage 1 with a ~200 mA current limit.
- **Nothing above 3.3 V ever goes to a XIAO pin** (other than its 5V pin). This matters in stage 7.
- LED_SUPPLY_SEL: one jumper only. 1-2 = 5 V (low current, ~29 mA max), 2-3 = 12 V.

### Handy measurement
LED current = voltage across R13 ÷ 4.7 Ω. **100 mV across R13 = 21 mA; 470 mV = 100 mA.** Easier and safer than putting the meter in series.

## 1. Power section only (`power.png`)
Build: J3 (or the 12 V lead) → D1 → C1, C2 → U2 (7805) → C3 → +5V_A; R1 + C4 → +5V_BIAS; D2 → XIAO_5V (XIAO **not** fitted yet). LED_SUPPLY_SEL jumper off.

**Option (breadboard): an external 5 V supply instead of U2.** Fine, as long as:
- **U2 isn't fitted at the same time.** Two supplies fighting over +5V_A, or 5 V back-driving an unpowered 7805, is bad news.
- **Its ground is joined to the 12 V ground.**
- **It measures 4.9-5.25 V.** +5V_A sets the brightness ceiling (5.25 V → ~101 mA), and the MCP6002/MCP4728 are rated to 5.5 V max.
- Keep C3 (10 µF) on +5V_A. If hum or whine appears in the pickups later, a noisy 5 V adapter is the first suspect; try the 7805 instead.

A beefy 5 V supply (≥ 0.5 A) also lets you try the **5 V-only LED option** properly in stage 2. Put a wire link in place of R12, select the 5 V position, and measure U3's collector-emitter voltage at the brightness you'd use.

| Check | Expect | Measured |
|---|---|---|
| VLED (after D1) | 11.5-11.8 V | |
| +5V_A | 4.8-5.2 V | |
| +5V_BIAS | ~ same as +5V_A, minus ~0.05 V | |
| XIAO_5V (D2 cathode) | +5V_A minus 0.2-0.4 V | |
| U2 temperature after 1 min | cold | |

## 2. Current sink only: U1B + U3 (`channel.png`, right half)
Build: U1 with power (pin 8 → +5V_A, pin 4 → GND, **C14 100 nF right across pins 8/4**). R9, R10, R11, C9, **R14 (1M, +5V_A → pin 6)**, U3, R13, R12, LED. Fit R15 (the trimmer), and for this stage only, **wire R15's wiper straight to R8** (instead of U1A pin 1). U1A is not used yet: tie pin 3 to GND, and pin 2 to pin 1, so it sits quietly.

**2a - 5 V position first** (LED_SUPPLY_SEL 1-2: the LED can't exceed ~29 mA whatever happens):

| Check | Expect | Measured |
|---|---|---|
| Trimmer at 0 V | LED off, V(R13) ≈ 0 | |
| U1 pin 5 with the trimmer at max | **≤ 0.45 V** (wiper ÷ 11). If it's near the wiper voltage, R8 and R9 are swapped or missing: 10k (brown-black-orange) goes from the wiper to pin 5, 1k (brown-black-red) from pin 5 to GND | |
| Trimmer slowly up | LED brightens smoothly; V(R13) ≈ wiper V ÷ 11 | |
| Trimmer at max | levels off at ~29 mA (R12 limiting; normal in this position) | |

If the LED is fully on at all settings or doesn't respond: check U1B pins 5/6 (+/−) and U3's E/C/B before going further.

**2b - 12 V position** (LED_SUPPLY_SEL 2-3):

| Check | Expect | Measured |
|---|---|---|
| Trimmer sweep | 0 → ~97 mA (V(R13) 0 → ~455 mV), smooth and linear | |
| At full: voltage U3 collector-emitter | ~3 V | |
| At full: U3 (BD139) after 1 min | warm, not too hot to touch | |
| At full: R12 | warm | |
| Stability: idle at mid brightness | steady reading; U3 not heating with nothing changing; no whine in the pickups | |

If you have a scope, look across R13 at mid brightness: it should be flat. Oscillation would show as a fuzzy band (hundreds of kHz).

**Optional, for the 5 V vs 12 V decision:** at the brightness you'd actually use, the collector-emitter voltage on U3 tells you how much headroom there is. Anything above ~0.5 V would also work from a 5 V-only supply.

## 3. Add the difference amp: U1A (`channel.png`, left half)
Build: remove the stage-2 links (pin 3 to GND, pin 2 to pin 1, wiper to R8). Add R4-R7, R2, R3, C7, C8, J1. R8 now goes from **U1A pin 1**. BIAS_SEL: jumper 2-3 (trimmer → Vbias → R7). Nothing plugged into J1.

| Check | Expect | Measured |
|---|---|---|
| U1 pin 1 vs BIAS_SEL pin 2 (Vbias) | equal, within ~10 mV (MCP6002) or ~30 mV (LM358); LM358 stops at ~3.5 V | |
| Trimmer sweep | LED 0 → full (MCP6002 ~97 mA, LM358 ~68 mA) | |
| U1 pins 2 and 3 | equal to each other, ≈ 0.9 × Vbias (the 1M bleeds pull them down a little) | |

**Optional polarity check:** temporarily link across C8, connect an AA cell + to the tip side and − to GND. The LED should get **brighter** (V1 rises by 1.5 V). Remove the link afterwards.

## 4. Audio through the link
Tascam line out → J1 (TRS lead); pickup → Tascam input. Trimmer at mid (~half brightness). Start with the Tascam output turned well down.

| Check | Expect | Measured |
|---|---|---|
| 1 kHz sine, raise level slowly | clean in the pickup until the peaks reach ±2.5 V (~+7 dBu), then it clips flat (LED off / full) | |
| Sweep 20 Hz-20 kHz | flat through the driver; the pickup and its ~50 Hz high-pass set the response | |
| Speech, noise | intelligible / sounds like noise | |
| No signal, listen for hum | quiet. Compare a TS vs TRS lead, and with the XIAO's USB in/out later | |
| Trimmer at 0 + audio | half-wave rectified, gated sound (expected) | |

## 5. Feedback
Pickup → Tascam → DAW (gain, filters) → line out → J1. Start with the DAW gain at minimum and the trimmer at mid, and bring the gain up slowly. Watch out for very loud squeals: keep your monitoring level low.

## 6. XIAO (U4)
Fit the XIAO: its 5V pin to XIAO_5V (D2 cathode), GND to GND. Flash any simple sketch (or the Peripheral firmware) **with WiFi/BLE off**.

| Check | Expect | Measured |
|---|---|---|
| XIAO 5V pin with USB unplugged | ~4.7 V, XIAO boots | |
| USB plugged in as well | still fine (D2 stops back-feeding) | |
| +5V_A while the XIAO runs | unchanged | |
| U2 (7805) temperature | warm at most (~0.5-0.8 W) | |
| Pickup at idle, LED at mid | no new whine or digital noise compared with stage 4 | |

## 7. DAC (`dac.png`)
Breadboard version:
- **MCP4728 breakout:** VCC → +5V_A, GND → GND. If it has an LDAC pin, tie it to GND.
- **Level-shifter module (BSS138 type):** HV → +5V_A, LV → XIAO 3V3, GND → GND. Low side ↔ XIAO D0 (SDA) and D1 (SCL); high side ↔ breakout SDA/SCL.
- **Warning:** the breakout has its own pull-ups to its VCC (5 V). Its SDA/SCL must **only** go to the shifter's high side, never straight to the XIAO.
- Smoothing on output A: 1k (R20) in series, 1 µF (C10) to GND → BIAS_SEL pin 1. Then move the BIAS_SEL jumper to 1-2.

Test sketch (Arduino / PlatformIO, Adafruit MCP4728 library):

```cpp
#include <Wire.h>
#include <Adafruit_MCP4728.h>

Adafruit_MCP4728 dac;

void setup() {
  Serial.begin(115200);
  Wire1.begin(1, 2);                       // SDA = GPIO1 (D0), SCL = GPIO2 (D1)
  if (!dac.begin(0x60, &Wire1)) {
    Serial.println("MCP4728 not found");
    while (true) delay(100);
  }
}

void loop() {
  // Slow triangle on channel A: 0..4095 = 0..5 V (VDD reference, gain 1)
  for (int v = 0; v < 4096; v += 16) {
    dac.setChannelValue(MCP4728_CHANNEL_A, v, MCP4728_VREF_VDD, MCP4728_GAIN_1X);
    delay(5);
  }
  for (int v = 4095; v >= 0; v -= 16) {
    dac.setChannelValue(MCP4728_CHANNEL_A, v, MCP4728_VREF_VDD, MCP4728_GAIN_1X);
    delay(5);
  }
}
```

| Check | Expect | Measured |
|---|---|---|
| Sketch starts without "not found" | DAC answering at 0x60 on Wire1 | |
| DAC_A (after R20/C10) | ramps 0 → ~5 V → 0, about 2.6 s per cycle | |
| LED (BIAS_SEL 1-2) | fades off → full → off | |
| Audio on top (stage 4 setup) | still works, riding on the DAC level | |
| Pickup during the ramp | no zipper/stepping noise (the 1k/1 µF should smooth it) | |

## 8. Later
- J2 → Central: network I2C on D4/D5, once the `LightChannel` Element exists in I2CElectronics (not started).
- Channels B-D on the PCB: BIAS_SEL pin 1 ← DAC_B/C/D.
