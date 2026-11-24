# linkmeasure - measuring the optical audio link

Plays test signals out of the soundcard into the LED driver, records what the photosensor sends back, and works out the link's frequency response, noise and distortion. Each run is saved in `runs/<date-time>_<label>/` with plots (PNG), data (CSV), the recordings (WAV) and a `summary.json`.

## Setup
- Soundcard output → LED driver input (J1); photosensor → soundcard input.
- Defaults: device name containing "Scarlett", **Out 1 → LED**, **In 1 ← photosensor**, 48 kHz. Change with `--device`, `--out`, `--in`.
- **Turn Direct Monitor off** on the interface. Otherwise the photosensor input is fed straight back to the outputs and the link becomes a feedback loop.
- Headphones or speakers on the interface hear the test signals too (outputs 1/2), so keep them down.
- Uses the SynthLearning virtualenv: `~/.virtualenvs/aotest/bin/python` (needs numpy, scipy, matplotlib, sounddevice).

## Commands
Run from this folder:

```bash
~/.virtualenvs/aotest/bin/python linkmeasure.py all --label mylabel --notes "bias mid, 10 cm"
```

| Command | What it does | Time |
|---|---|---|
| `all` | sweep + noise + tones + levels | ~1 min |
| `sweep` | exponential sine sweep 20 Hz-20 kHz → frequency response (`response.png/csv`) | ~10 s |
| `noise` | 10 s with the output silent (LED at idle bias) → noise spectrum, total noise, mains lines (`noise.png`, `noise_psd.csv`) | ~10 s |
| `tones` | 100 Hz, 1 kHz, 5 kHz → level back, THD, THD+N, SNR (`tones.csv`) | ~5 s |
| `levels` | 1 kHz from −50 dBFS up to `--max-level` → compression and distortion vs drive (`levels.png/csv`) | ~30 s |
| `biassweep --dac auto` | steps the LED bias through the DAC (codes `--bias-from`..`--bias-to` in `--bias-step`s, default 100-2200 step 150) and measures gain, THD and noise at each (`bias_sweep.png/csv`) | ~1 min |
| `compare RUN RUN ...` | overlays up to 6 runs: responses relative to 1 kHz, noise relative to signal (noise minus each run's gain - needs a sweep in the run), and THD / THD+N vs drive level (runs with a `levels` ramp; clipped points left out). `--absolute` plots raw gains and dBFS | |
| `replot RUN ...` | redraws a run's plots from its saved data | |
| `reanalyse RUN ...` | recomputes a run's frequency response from its saved `sweep_recorded.wav` with the current analysis. It rewrites `response.csv` / `.png` and the sweep numbers in `summary.json`, and keeps the old numbers under `sweep.before_reanalysis` | |
| `summarise RUN ...` | one table of key numbers across runs (gain, −3 dB points, noise, noise relative to signal, 50 Hz, THD) → `runs/summary_*.md/.csv` | |
| `devices` | lists audio devices | |

Useful options: `--level` (sweep/tone level, dBFS peak, default −20), `--max-level` (top of the `levels` ramp, default 0), `--sweep-secs`, `--noise-secs`, `--notes` (saved in summary.json), `--monitor N` (`noise`, and the noise step of `all`: also record input N at the same time, e.g. `--monitor 2` with In 2 across R13 to see the LED current. A sweep recorded on both inputs first gives the transfer from N to the photosensor input, so the plot also shows N's noise *referred to In 1*. Where that line meets In 1's, In 1's noise is already in what N sees; where In 1 sits higher, it's added after that point). Noise summaries list the strongest spectral peaks (tones and oscillations standing out of the floor). Input clipping is reported as it happens, and marked ✕ on the levels plot.

**Bias from the DAC:** with BIAS_SEL on the DAC (1-2) and the Feather (or other board) running the `dac_test` firmware on USB, `--dac auto` finds its serial port (a USB-serial chip such as the Feather's CP2104), and `--bias CODE` sets the bias before any measurement (recorded in summary.json), e.g. `all --dac auto --bias 1000`. Opening the port resets the board, so the LED ramps for a couple of seconds before the bias is set. With the current (probably counterfeit) op-amp, codes above ~2200 make no difference (V1 stops at ~1.8 V).

**Noise history:** `~/.virtualenvs/aotest/bin/python noise_history.py` redraws the stage-by-stage noise comparison: Oct 24 old op-amp → new op-amp → new supply → housing → 9 V battery → laptop off its charger. Outputs are `runs/noise_history_spectra.png` (one panel per change, before vs after), `runs/noise_history_bands.png` (total and per-band noise at each stage) and `runs/noise_history.md/.csv`. To add or swap a stage, edit `STAGES` at the top of the script.

**DAC update noise:** `~/.virtualenvs/aotest/bin/python dacnoise.py --dac /dev/cu.SLAB_USBtoUART --code 450` records the noise (In 1 + In 2) four ways at one bias:
- steady;
- USB serial traffic only;
- the same code rewritten at `--rate` per second (I2C traffic, unchanged output);
- a slow ramp of ±`--span` codes over `--period` s.

It shows what bias writes, ramps and LFOs cost in noise, and saves `dac_noise.png` plus per-case PSDs.

`compare` orders runs by folder name (date-time), whatever order you give them in. The newest gets the first colour, is drawn on top, and heads the legend.

**Analysis fix (2026-11-19):** before this date, the sweep analysis started its window 10 ms before the impulse peak. That cut off the low-frequency pre-ringing and drew a ~100 Hz-spaced ripple (about ±0.2 dB) into 100-500 Hz. It also put the low −3 dB point ~7-9 Hz too high. The window now starts 100 ms before the peak. Runs measured before then still carry the ripple until you `reanalyse` them.

## Reading the results
- **Response plots** are drawn relative to the gain at 1 kHz, so the −3 dB line really is 3 dB below the middle of the band. The **absolute gain** (in the caption, in `response.csv` and in `summary.json`) is relative to digital loopback: 0 dB means the signal comes back at the level it was sent. It depends on the interface's output and input gain knobs, so compare absolute gains only with the knobs untouched.
- **Noise** is measured with silence on the output, so it includes the LED's idle light (shot noise), room lighting, hum, the pickup and the preamp.
- **THD** = harmonic distortion only; **THD+N** includes noise; **SNR** = the tone vs everything else in 20 Hz-20 kHz.
- **Round-trip time** includes the computer's audio buffers, so it isn't the link's delay (light is effectively instant).

## Useful experiments
- **Driver only (electrical):** measure the voltage across R13 on **In 2**, then `noise --monitor 2` (both at once) or `all --in 2 --label driver`. This separates the LED driver from the optics and the pickup. **Use a TRS lead: tip = top of R13, ring = bottom of R13 (at R13), shield not connected at the board end.** A TS lead (sleeve to board GND) adds a second ground path to the interface and injects 50 Hz hum into the LED current (seen 2026-10-24).
- **Lights off / pickup shaded:** `noise --label lights_off` vs `noise --label lights_on` → is the 50 Hz comb room lighting?
- **Bias:** runs at low, mid and high trimmer settings, then `compare`.
- **Distance / angle / glass in the beam:** one run each, then `compare`.
