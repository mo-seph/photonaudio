# MCP4728 DAC test (XIAO ESP32-C6 / S3, or HUZZAH32 Feather)

Standalone test of the LED driver's bias DAC: finds the MCP4728 on I2C, then ramps channel A up and down so the LED fades, with simple serial commands for fixed levels. Not the Peripheral firmware.

## Build and upload

From this folder:

```bash
~/.platformio/penv/bin/pio run -e xiao-c6 -t upload
```

```bash
~/.platformio/penv/bin/pio device monitor -e xiao-c6
```

`xiao-s3` builds the same sketch for the XIAO ESP32-S3, and `feather-esp32` for the Adafruit HUZZAH32 ESP32 Feather (both on espressif32 6.9.0 / arduino-esp32 2.0.17). `xiao-s3-board` is the PCB's wiring on the S3: see "Board wiring test" below.

**Why two platforms:** the C6 needs arduino-esp32 v3.x, which the official PlatformIO platform doesn't provide for C6 (ESP-IDF only), so `xiao-c6` uses the **pioarduino** platform, pinned to release 55.03.312 (arduino-esp32 3.3.12). `xiao-s3` uses the same platform as I2CElectronics (espressif32 6.9.0, arduino-esp32 2.0.17). Both build cleanly (2026-10-22).

## Wiring (no level shifter)

| MCP4728 breakout | XIAO ESP32-C6 |
|---|---|
| VCC (VIN) | **3V3** |
| GND | GND |
| SDA | D4 (GPIO22) |
| SCL | D5 (GPIO23) |
| LDAC (if present) | GND |

### HUZZAH32 Feather (`feather-esp32`), with the LED driver's 3.3 V rail powering the DAC

| MCP4728 breakout | Connect to |
|---|---|
| VCC (VIN) | **+3V3_A** on the breadboard (the LD33 output) |
| GND | breadboard GND; Feather GND only when the Feather is **not** on the laptop's USB (see below) |
| SDA | Feather **SDA** (GPIO23) |
| SCL | Feather **SCL** (GPIO22) |
| LDAC (if present) | GND |

The Feather is powered from its own USB, and only ground, SDA and SCL go between it and the breadboard. The breakout's pull-ups then go to +3V3_A, which is 3.3 V, so they're safe for the ESP32. Have both powered when testing: an unpowered board with the other one driving the bus leaks current through the pins' protection diodes.

**Ground (2026-11-04):** with the Feather on the laptop's USB, its ground already reaches the breadboard through the laptop, the Scarlett and the audio cables. A Feather-to-breadboard GND wire then closes a ground loop: 120 Hz and 434 / 1302 / 1592 Hz lines in the LED current, about 15 dB more noise. So with USB, leave that wire out. Only fit it when the Feather runs from a power bank. Without it, the I2C return current takes the long way, and DAC writes add a stronger 500 Hz comb. The PCB avoids both, because the XIAO sits next to the DAC and isn't on USB during use. Dave's breadboard bus has no pull-up resistors; the ESP32's internal ones are enough on a short run.

### DAC output, any board
DAC output A → 1k (R20) → BIAS_SEL pin 1, with 1 µF (C10) from there to GND (a 0.47 µF electrolytic is fine: + towards R20, − to GND). Jumper BIAS_SEL 1-2.

**Power the breakout from 3.3 V, not 5 V.** The breakout has its own pull-up resistors on SDA/SCL, tied to its VCC. At 5 V they'd hold the bus at 5 V, and the C6's pins are 3.3 V only (they can be damaged). Even with the pull-ups removed, a 5 V MCP4728 officially needs more than 3.5 V for a logic high, so it might or might not respond to 3.3 V signals.

At 3.3 V everything is in spec. On the 3.3 V version of the driver (R9 = 1.6k, 2026-10-23) the DAC's 0-3.3 V range is the full range, so the DAC alone reaches full current (~95 mA). (On the old 5 V driver it only reached ~64 mA.)

## Serial commands (one per line)

| Command | Effect |
|---|---|
| `a 2048` | set channel A (0-4095); also `b`, `c`, `d`. Stops the ramp |
| `all 1000` | set all four channels |
| `ramp 4000` | triangle ramp on A with that period in ms (default at boot: 4000) |
| `stop` | hold the current value |
| `ref int` / `ref vdd` | DAC reference: the internal 2.048 V (0.5 mV steps, output tops out at 2.048 V) or VDD (default, 0.8 mV steps). Re-sends the current values. Resets to `vdd` when the board restarts |
| `check 10000` | writes that many pseudo-random values (cycling A-D), reads each one back, and prints the write failures, read failures and wrong values. Stops the ramp; puts the previous values back afterwards. The LED flickers while it runs |
| `speed 400000` | DAC bus clock in Hz (100 kHz at boot) |
| `stats` | DAC writes and failed writes since boot (the ramp counts too), plus the network slave's receive / request counts in `xiao-s3-board` |
| `scan` | list I2C devices on the DAC bus; retries the DAC if it wasn't found |
| `?` | help |

## Expected
- At boot: "device at 0x60 (MCP4728)", then "MCP4728 found - ramping channel A".
- DAC output A (before the 1k): 0 → 3.3 V → 0 every 4 s. LED fades between off and ~⅔ brightness.
- `a 4095` → about 3.3 V; `a 0` → 0 V, LED fully off (thanks to R14).

## Board wiring test (`xiao-s3-board`, 2026-11-06)

On the PCB the DAC is on the XIAO's D0 / D1, not on the usual I2C pins. That's not software I2C: the S3 has two hardware I2C controllers, and the second one (`Wire1`) is routed to D0 / D1. The Peripheral firmware keeps `Wire` as the network slave on D4 / D5. Nothing in this project has run both controllers at once yet, so this env does just that: DAC master on `Wire1`, plus a stand-in slave on `Wire` at 0x13 (it answers 0xAA, like I2CElectronics' `peripheral-s3-test`).

```bash
~/.platformio/penv/bin/pio run -e xiao-s3-board -t upload
```

```bash
~/.platformio/penv/bin/pio device monitor -e xiao-s3-board
```

Wiring, as on the PCB:

| XIAO ESP32-S3 | Connect to |
|---|---|
| D0 (GPIO1) | 220 Ω (R27) → DAC SDA |
| D1 (GPIO2) | 220 Ω (R28) → DAC SCL |
| 3V3 | DAC VCC; 10k (R16 / R17) from DAC SDA and DAC SCL |
| GND | DAC GND, LDAC |
| D4 / D5 | nothing; or a Central's bus for the optional step |

**XIAO ESP32-C3 (`xiao-c3`):** use the same wiring (the C3's D0 / D1 are GPIO2 / GPIO3). The C3 has only one I2C controller, so this build puts the DAC on `Wire` and has no network slave. It checks the wiring, the series resistors and the DAC (`check`, voltages, `stats`), but not the S3's `Wire1` or both controllers at once. Those, and the real firmware, need an S3. A C3 can't run the board: one controller can't be the network slave and the DAC master at the same time.

The pull-ups go on the DAC side of the 220 Ω resistors. With the DAC run from the XIAO's 3V3 and no driver attached, there's no ground loop to worry about; check the outputs with a meter.

| Step | Expect | Result |
|---|---|---|
| Boot | `network slave 0x13 ... started`, `device at 0x60 (MCP4728)`, `MCP4728 found` | |
| `check 10000` (100 kHz, ~30 s) | 0 write failures, 0 read failures, 0 wrong values | |
| `a 4095` / `a 2048` / `a 0` | DAC A ≈ 3.3 V / 1.65 V / 0 V | |
| ramp for a few minutes, then `stats` | 0 failed | |
| `speed 400000`, `check 10000` (~10 s) | 0 errors. Only a bonus: the board runs at 100 kHz, and a breadboard's capacitance can make 400 kHz marginal with 10k pull-ups | |
| Optional: Central on D4 / D5 with `scan_interval 2000`, during a `check` | 0x13 appears in the Central's scan, the `stats` request count rises, and the check still shows 0 errors | |

## Note for the board design
The C6 has only **one** full I2C controller. arduino-esp32 3.x exposes its low-power I2C controller as `Wire1`, but that one has restrictions (in ESP-IDF it is master-only and limited to particular pins). The S3 has two full controllers. So the plan of "network I2C slave on `Wire` + DAC master on `Wire1`" needs checking before the LED board commits to a C6.
