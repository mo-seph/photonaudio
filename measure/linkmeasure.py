"""Measure the optical audio link: soundcard out -> LED driver -> light -> photosensor -> soundcard in.

Subcommands (each saves into runs/<timestamp>_<label>/):
  devices                 list audio devices
  sweep                   frequency response from an exponential sine sweep
  noise                   noise spectrum with silence on the output (LED at its idle bias)
  tones                   distortion and signal-to-noise at a few frequencies
  levels                  output level and distortion vs input level at 1 kHz (shows clipping)
  all                     sweep + noise + tones + levels
  compare RUN [RUN ...]   overlay the frequency responses and noise spectra of earlier runs
  replot RUN [RUN ...]    redraw a run's plots from its saved data
  reanalyse RUN [RUN ...] recompute a run's frequency response from its saved sweep_recorded.wav
                          (rewrites response.csv/.png and the sweep numbers in summary.json; the old
                          numbers are kept under sweep.before_reanalysis)

Levels are in dBFS (peak for outputs, rms for measurements). Absolute gains are relative to
digital loopback: 0 dB means the signal comes back at the same level it was sent. Response
plots are drawn relative to the 1 kHz gain, so the −3 dB line is at −3 dB.

Run with the SynthLearning virtualenv:  ~/.virtualenvs/aotest/bin/python linkmeasure.py all --label first
"""
import argparse
import csv
import datetime
import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
import sounddevice as sd
from scipy import signal

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
RUNS = HERE / 'runs'

# Chart styling: light surface (readable in dark-mode viewers), one accent colour, neutral inks.
SURFACE, INK, INK2, GRID = '#fcfcfb', '#0b0b0b', '#52514e', '#e4e3df'
SERIES = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300']


@dataclass
class Rig:
    device: str = 'Scarlett'
    out_ch: int = 1          # 1-based soundcard output feeding the LED driver
    in_ch: int = 1           # 1-based soundcard input from the photosensor
    fs: int = 48000


# ---- Audio I/O ------------------------------------------------------------------------------

def find_device(name):
    for i, d in enumerate(sd.query_devices()):
        if name.lower() in d['name'].lower() and d['max_input_channels'] > 0 and d['max_output_channels'] > 0:
            return i
    raise SystemExit(f'No duplex audio device matching "{name}" - run "devices" to list them')


def playrec_multi(rig, out, inputs):
    """Play a mono signal on rig.out_ch and record the given 1-based inputs; returns (samples, len(inputs))."""
    rec = sd.playrec(out.astype('float32').reshape(-1, 1), samplerate=rig.fs, device=find_device(rig.device),
                     input_mapping=list(inputs), output_mapping=[rig.out_ch], dtype='float32', latency='low')
    # Wait for the stream with a timeout: an audio device that stops delivering (reset, another app
    # grabbing it) would otherwise hang sd.wait() forever.
    deadline = time.time() + len(out) / rig.fs + 5.0
    while sd.get_stream().active:
        if time.time() > deadline:
            sd.stop()
            raise SystemExit('Audio stream stalled (device reset or busy?) - re-run the command')
        time.sleep(0.05)
    return rec.astype(float)


CLIP_LEVEL = 0.98   # recorded peaks at or above this (≈ −0.2 dBFS) count as input clipping


def playrec(rig, out):
    """Play a mono signal on rig.out_ch and return what comes back on rig.in_ch."""
    rec = playrec_multi(rig, out, [rig.in_ch])[:, 0]
    if np.max(np.abs(rec)) >= CLIP_LEVEL:
        print(f'  ! input clipped (peak {db(np.max(np.abs(rec))):.1f} dBFS) - turn the input gain or the drive level down')
    return rec


def db(x, floor=1e-12):
    return 20 * np.log10(np.maximum(np.abs(x), floor))


def rms(x):
    return np.sqrt(np.mean(np.square(x)))


# ---- Bias control via the DAC test firmware (dac_test/, serial command "a <code>") ----------------

class Dac:
    """Sets the LED bias through the MCP4728 test firmware over USB serial (BIAS_SEL on the DAC)."""

    def __init__(self, port):
        import serial
        self.port = find_dac_port() if port == 'auto' else port
        self.serial = serial.Serial(self.port, 115200, timeout=1)
        time.sleep(2.5)                      # opening the port resets the board; let it boot
        self.serial.reset_input_buffer()

    def set(self, code):
        self.serial.write(f'a {int(code)}\n'.encode())
        reply = self.serial.readline().decode(errors='replace').strip()
        if not reply.replace(' ', '').startswith('a='):     # firmware prints "a = 400" or "a= 400"
            raise SystemExit(f'DAC did not confirm "a {code}" (got "{reply}") - is the dac_test firmware running?')
        time.sleep(0.3)                      # R20/C10 settle in ~ms; give the LED and pickup a moment too

    def close(self):
        self.serial.close()


def find_dac_port():
    from serial.tools import list_ports
    hints = ('cp210', 'uart', 'usbserial', 'usb serial', 'slab')
    for p in list_ports.comports():
        if any(h in (p.description + ' ' + p.device).lower() for h in hints):
            return p.device
    ports = ', '.join(p.device for p in list_ports.comports())
    raise SystemExit(f'No USB-serial board found for the DAC (ports: {ports}) - pass --dac /dev/cu.xxx')


# ---- Frequency response (Farina exponential sweep) -----------------------------------------------

def make_sweep(fs, f1, f2, secs, level_db):
    t = np.arange(int(secs * fs)) / fs
    rate = np.log(f2 / f1)
    sweep = np.sin(2 * np.pi * f1 * secs / rate * (np.exp(t * rate / secs) - 1))
    fade = signal.windows.tukey(len(sweep), alpha=0.02)
    sweep *= fade * 10 ** (level_db / 20)
    inverse = sweep[::-1] * np.exp(-t * rate / secs)
    return sweep, inverse


def octave_smooth(freqs, mag_db, fraction=6):
    """Smooth a magnitude response over 1/fraction-octave bands (power average)."""
    power = 10 ** (mag_db / 10)
    out = np.empty_like(mag_db)
    for i, f in enumerate(freqs):
        lo, hi = f * 2 ** (-0.5 / fraction), f * 2 ** (0.5 / fraction)
        band = (freqs >= lo) & (freqs <= hi)
        out[i] = 10 * np.log10(power[band].mean()) if band.any() else mag_db[i]
    return out


def deconvolve(rec, out, inverse, fs, f1, f2):
    """Farina deconvolution of one recorded sweep: complex response over f1..f2, and delay vs the stimulus (ms)."""
    ir = signal.fftconvolve(rec, inverse)
    ref = signal.fftconvolve(out, inverse)
    p_ir, p_ref = int(np.argmax(np.abs(ir))), int(np.argmax(np.abs(ref)))

    # Window the linear part. The harmonic distortion responses sit earlier (2nd harmonic:
    # secs * ln 2 / ln(f2/f1), 0.8 s for an 8 s sweep), so start the window up to 100 ms before the
    # peak, staying inside half that gap. A 10 ms start (used until 2026-11-19) cut off the band-limited
    # impulse's low-frequency pre-ringing and drew a ~100 Hz-spaced ripple into 100-500 Hz.
    secs = len(inverse) / fs
    pre = int(min(0.1, 0.5 * secs * np.log(2) / np.log(f2 / f1)) * fs)
    post = int(0.3 * fs)
    taper = np.concatenate([np.ones(pre + post // 2), np.hanning(post)[post // 2:]])
    win = lambda x, p: x[p - pre:p + post] * taper
    n = 2 ** int(np.ceil(np.log2(pre + post)) + 1)
    h = np.fft.rfft(win(ir, p_ir), n) / np.fft.rfft(win(ref, p_ref), n)
    freqs = np.fft.rfftfreq(n, 1 / fs)
    band = (freqs >= f1) & (freqs <= f2)
    return freqs[band], h[band], (p_ir - p_ref) / fs * 1000


def measure_sweep(rig, level_db=-20, f1=20, f2=20000, secs=8.0):
    sweep, _ = make_sweep(rig.fs, f1, f2, secs, level_db)
    rec = playrec(rig, np.concatenate([sweep, np.zeros(int(1.5 * rig.fs))]))
    return analyse_sweep(rec, rig.fs, level_db, f1, f2, secs)


def analyse_sweep(rec, fs, level_db, f1, f2, secs):
    """Frequency response from a recorded sweep (also used by `reanalyse` on a saved sweep_recorded.wav)."""
    sweep, inverse = make_sweep(fs, f1, f2, secs, level_db)
    out = np.concatenate([sweep, np.zeros(int(1.5 * fs))])
    freqs, h, latency_ms = deconvolve(rec, out, inverse, fs, f1, f2)
    mag = db(h)
    smooth = octave_smooth(freqs, mag)

    gain_1k = float(np.interp(1000, freqs, smooth))
    passband = freqs[smooth >= gain_1k - 3]
    return {
        'level_dbfs': level_db, 'f1': f1, 'f2': f2, 'secs': secs,
        'latency_ms': round(latency_ms, 2),
        'gain_1k_db': round(gain_1k, 2),
        'minus3db_low_hz': round(float(passband.min()), 1) if passband.size else None,
        'minus3db_high_hz': round(float(passband.max()), 1) if passband.size else None,
        '_freqs': freqs, '_mag': mag, '_smooth': smooth, '_rec': rec, '_stim': out,
    }


def measure_transfer(rig, monitor, level_db=-30, f1=20, f2=20000, secs=8.0):
    """Response from input `monitor` to rig.in_ch (dB, 1/6-octave smoothed), from one sweep recorded on both.
    Adding it to the monitor's noise spectrum refers that noise to the photosensor input: where the two
    match, the photosensor's noise is already in what the monitor sees (e.g. the LED current on R13)."""
    sweep, inverse = make_sweep(rig.fs, f1, f2, secs, level_db)
    out = np.concatenate([sweep, np.zeros(int(1.5 * rig.fs))])
    rec = playrec_multi(rig, out, [rig.in_ch, monitor])
    for col, ch in enumerate((rig.in_ch, monitor)):
        if np.max(np.abs(rec[:, col])) >= CLIP_LEVEL:
            print(f'  ! In {ch} clipped during the transfer sweep - turn its gain or --level down')
    freqs, h_main, _ = deconvolve(rec[:, 0], out, inverse, rig.fs, f1, f2)
    _, h_mon, _ = deconvolve(rec[:, 1], out, inverse, rig.fs, f1, f2)
    return freqs, octave_smooth(freqs, db(h_main) - db(h_mon))


# ---- Noise ---------------------------------------------------------------------------------------

def a_weighting_db(f):
    f2 = np.square(np.asarray(f, dtype=float))
    ra = (12194 ** 2 * f2 ** 2) / ((f2 + 20.6 ** 2) * np.sqrt((f2 + 107.7 ** 2) * (f2 + 737.9 ** 2)) * (f2 + 12194 ** 2))
    return db(ra) + 2.0


def noise_stats(rec, fs):
    """Spectrum and summary numbers for one recorded channel."""
    freqs, psd = signal.welch(rec, fs, nperseg=fs, window='hann')   # 1 Hz bins, FS^2/Hz
    df = freqs[1] - freqs[0]
    band = (freqs >= 20) & (freqs <= 20000)
    total = 10 * np.log10(psd[band].sum() * df)
    weighted = 10 * np.log10((psd[band] * 10 ** (a_weighting_db(freqs[band]) / 10)).sum() * df)
    hum = {}
    for k in range(1, 7):
        f0 = 50 * k
        near = (freqs >= f0 - 2) & (freqs <= f0 + 2)
        hum[f'{f0}Hz'] = round(float(10 * np.log10(psd[near].sum() * df)), 1)
    # Peaks standing well clear of the local floor (tones, oscillations), strongest first
    level = 10 * np.log10(psd + 1e-30)
    floor = signal.medfilt(level, 101)
    idx, _ = signal.find_peaks(level - floor, height=12, distance=20)
    idx = [i for i in idx if 20 <= freqs[i] <= 20000]
    idx = sorted(idx, key=lambda i: level[i], reverse=True)[:6]
    peaks = [{'hz': round(float(freqs[i]), 1), 'dbfs_per_hz': round(float(level[i]), 1),
              'above_floor_db': round(float(level[i] - floor[i]), 1)} for i in idx]
    return {'rms_dbfs_20_20k': round(float(total), 1), 'rms_dbfs_a_weighted': round(float(weighted), 1),
            'hum_dbfs': hum, 'peaks': peaks}, freqs, psd


def measure_noise(rig, secs=10.0, monitor=None):
    """Record with the output silent. With monitor=N, also record input N at the same time
    (e.g. the voltage across R13, i.e. the LED current) and analyse it the same way."""
    inputs = [rig.in_ch] + ([monitor] if monitor else [])
    rec = playrec_multi(rig, np.zeros(int(secs * rig.fs)), inputs)[int(0.5 * rig.fs):]
    stats, freqs, psd = noise_stats(rec[:, 0], rig.fs)
    res = dict(secs=secs, **stats, _freqs=freqs, _psd=psd, _rec=rec[:, 0])
    if monitor:
        mstats, _, mpsd = noise_stats(rec[:, 1], rig.fs)
        res.update(monitor_in=monitor, monitor=mstats, _psd_monitor=mpsd, _rec_monitor=rec[:, 1])
    return res


# ---- Tones: least-squares sine fit (play and record share a clock, so frequencies are exact) -------

def analyse_tone(y, fs, f0, n_harm=5):
    t = np.arange(len(y)) / fs
    cols = [np.ones_like(t)]
    for k in range(1, n_harm + 1):
        cols += [np.cos(2 * np.pi * k * f0 * t), np.sin(2 * np.pi * k * f0 * t)]
    basis = np.stack(cols, axis=1)
    coef, *_ = np.linalg.lstsq(basis, y, rcond=None)
    amps = np.hypot(coef[1::2], coef[2::2]) / np.sqrt(2)          # rms of each harmonic
    fit = basis @ coef
    residual = y - fit
    sos = signal.butter(4, [20, min(20000, 0.45 * fs)], btype='bandpass', fs=fs, output='sos')
    noise = rms(signal.sosfiltfilt(sos, residual))
    harm_rms = np.sqrt(np.sum(np.square(amps[1:])))
    return {
        'f0': f0,
        'fundamental_dbfs': round(float(db(amps[0])), 2),
        'harmonics_dbc': [round(float(db(a / amps[0])), 1) for a in amps[1:]],
        'thd_pct': round(float(100 * harm_rms / amps[0]), 3),
        'thd_n_pct': round(float(100 * np.hypot(harm_rms, noise) / amps[0]), 3),
        'snr_db': round(float(db(amps[0] / noise)), 1),
    }


def play_tone(rig, f0, level_db, secs=1.5):
    t = np.arange(int(secs * rig.fs)) / rig.fs
    tone = 10 ** (level_db / 20) * np.sin(2 * np.pi * f0 * t) * signal.windows.tukey(len(t), 0.05)
    rec = playrec(rig, np.concatenate([tone, np.zeros(int(0.2 * rig.fs))]))
    start, stop = int(0.3 * rig.fs), int((secs - 0.2) * rig.fs)   # steady middle part
    return rec[start:stop]


def measure_tones(rig, freqs=(100, 1000, 5000), level_db=-20):
    return [dict(analyse_tone(play_tone(rig, f, level_db), rig.fs, f), level_dbfs=level_db) for f in freqs]


def measure_bias_sweep(rig, dac, codes, level_db=-30, f0=1000, noise_secs=2.0):
    """At each DAC bias code: a 1 kHz tone (level back, gain, THD) and a short silent recording (noise)."""
    rows = []
    for code in codes:
        dac.set(code)
        r = analyse_tone(play_tone(rig, f0, level_db), rig.fs, f0)
        stats, _, _ = noise_stats(playrec(rig, np.zeros(int(noise_secs * rig.fs)))[int(0.3 * rig.fs):], rig.fs)
        rows.append(dict(code=int(code), dac_volts=round(code / 4095 * 3.3, 3), level_dbfs=level_db,
                         gain_db=round(r['fundamental_dbfs'] - (level_db - 3.01), 2),   # rms back vs rms sent
                         thd_pct=r['thd_pct'], thd_n_pct=r['thd_n_pct'],
                         h2_dbc=r['harmonics_dbc'][0], h3_dbc=r['harmonics_dbc'][1],
                         noise_dbfs=stats['rms_dbfs_20_20k'], snr_db=round(r['fundamental_dbfs'] - stats['rms_dbfs_20_20k'], 1)))
        print(f"  code {code}: gain {rows[-1]['gain_db']:+.1f} dB, THD {r['thd_pct']}%, noise {stats['rms_dbfs_20_20k']} dBFS")
    return rows


def measure_levels(rig, f0=1000, lo=-50, hi=0, step=2):
    rows = []
    for level in np.arange(lo, hi + 0.01, step):
        y = play_tone(rig, f0, level, secs=1.0)
        r = analyse_tone(y, rig.fs, f0)
        rows.append(dict(level_dbfs=float(level), input_clipped=bool(np.max(np.abs(y)) >= CLIP_LEVEL), **r))
    return rows


# ---- Plots -----------------------------------------------------------------------------------------

def styled_axes(title, xlabel, ylabel, logx=True):
    fig, ax = plt.subplots(figsize=(8, 4.2), dpi=150)
    fig.patch.set_facecolor(SURFACE); ax.set_facecolor(SURFACE)
    if logx:
        ax.set_xscale('log')
        ax.set_xticks([20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000])
        ax.set_xticklabels(['20', '50', '100', '200', '500', '1k', '2k', '5k', '10k', '20k'])
    ax.set_title(title, color=INK, fontsize=11, loc='left')
    ax.set_xlabel(xlabel, color=INK2); ax.set_ylabel(ylabel, color=INK2)
    ax.grid(True, which='major', color=GRID, linewidth=0.8); ax.set_axisbelow(True)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    for s in ('left', 'bottom'):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=INK2)
    return fig, ax


def save(fig, path):
    fig.tight_layout()
    fig.savefig(path, facecolor=SURFACE)
    plt.close(fig)


def plot_response(res, path, label):
    """Response relative to 1 kHz (0 dB there); the absolute gain is given in the caption."""
    g = res['gain_1k_db']
    fig, ax = styled_axes(f'Frequency response - {label}', 'Frequency (Hz)', 'Gain relative to 1 kHz (dB)')
    ax.plot(res['_freqs'], res['_mag'] - g, color=SERIES[0], linewidth=0.6, alpha=0.25)
    ax.plot(res['_freqs'], res['_smooth'] - g, color=SERIES[0], linewidth=2)
    ax.axhline(-3, color=INK2, linewidth=1, linestyle=(0, (4, 3)))
    ax.text(25, -2.6, '−3 dB', color=INK2, fontsize=9)
    ax.set_xlim(res['f1'], res['f2']); ax.set_ylim(-30, 10)
    lo, hi = res['minus3db_low_hz'], res['minus3db_high_hz']
    ax.text(0.99, 0.04, f"−3 dB: {lo:.0f} Hz – {hi / 1000:.1f} kHz    absolute gain at 1 kHz {g:+.1f} dB re loopback",
            transform=ax.transAxes, ha='right', color=INK, fontsize=9)
    save(fig, path)


def plot_noise(res, path, label):
    fig, ax = styled_axes(f'Noise spectrum, output silent - {label}', 'Frequency (Hz)', 'Noise density (dBFS/Hz)')
    band = (res['_freqs'] >= 20) & (res['_freqs'] <= 20000)
    ax.plot(res['_freqs'][band], 10 * np.log10(res['_psd'][band] + 1e-30), color=SERIES[0], linewidth=1,
            label=f"In {res.get('in_ch', '')} (photosensor)".replace('In  ', 'In '))
    if '_psd_monitor' in res:
        mon = 10 * np.log10(res['_psd_monitor'][band] + 1e-30)
        referred = '_transfer_db' in res
        ax.plot(res['_freqs'][band], mon, color=SERIES[1], linewidth=1, alpha=0.45 if referred else 1,
                label=f"In {res['monitor_in']} (monitor, as recorded)")
        if referred:
            ax.plot(res['_freqs'][band], mon + res['_transfer_db'][band], color=SERIES[2], linewidth=1,
                    label=f"In {res['monitor_in']} referred to In {res.get('in_ch', 1)} (× measured transfer)")
        ax.legend(frameon=False, fontsize=9, labelcolor=INK, loc='lower left')
    ax.set_xlim(20, 20000)
    ax.text(0.99, 0.94, f"total {res['rms_dbfs_20_20k']} dBFS (20 Hz–20 kHz),  {res['rms_dbfs_a_weighted']} dBFS(A)",
            transform=ax.transAxes, ha='right', color=INK, fontsize=9)
    worst = max(res['hum_dbfs'].items(), key=lambda kv: kv[1])
    ax.text(0.99, 0.87, f"largest mains line: {worst[0]} at {worst[1]} dBFS", transform=ax.transAxes,
            ha='right', color=INK, fontsize=9)
    save(fig, path)


def plot_levels(rows, path, label):
    level = [r['level_dbfs'] for r in rows]
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(8, 6.5), dpi=150, sharex=True)
    fig.patch.set_facecolor(SURFACE)
    for ax in (a1, a2):
        ax.set_facecolor(SURFACE); ax.grid(True, color=GRID, linewidth=0.8); ax.set_axisbelow(True)
        for s in ('top', 'right'):
            ax.spines[s].set_visible(False)
        for s in ('left', 'bottom'):
            ax.spines[s].set_color(GRID)
        ax.tick_params(colors=INK2)
    a1.plot(level, [r['fundamental_dbfs'] for r in rows], color=SERIES[0], linewidth=2, marker='o', markersize=4)
    a1.set_ylabel('Level back (dBFS rms)', color=INK2)
    a1.set_title(f'Level and distortion vs drive at 1 kHz - {label}', color=INK, fontsize=11, loc='left')
    a2.plot(level, [r['thd_n_pct'] for r in rows], color=SERIES[0], linewidth=2, marker='o', markersize=4)
    clipped = [r for r in rows if r.get('input_clipped')]
    if clipped:
        for ax, key in ((a1, 'fundamental_dbfs'), (a2, 'thd_n_pct')):
            ax.plot([r['level_dbfs'] for r in clipped], [r[key] for r in clipped], linestyle='none', marker='x',
                    markersize=9, color=INK, label='input clipped')
        a2.legend(frameon=False, fontsize=9, labelcolor=INK)
    a2.set_yscale('log')
    a2.set_ylabel('THD+N (%)', color=INK2)
    a2.set_xlabel('Drive level sent to Out (dBFS peak)', color=INK2)
    save(fig, path)


def plot_bias_sweep(rows, path, label):
    code = [r['code'] for r in rows]
    panels = [('gain_db', 'Gain at 1 kHz (dB)', False), ('thd_pct', 'THD (%)', True), ('noise_dbfs', 'Noise (dBFS, 20 Hz–20 kHz)', False)]
    fig, axes = plt.subplots(len(panels), 1, figsize=(8, 8), dpi=150, sharex=True)
    fig.patch.set_facecolor(SURFACE)
    for ax, (key, ylabel, logy) in zip(axes, panels):
        ax.set_facecolor(SURFACE); ax.grid(True, color=GRID, linewidth=0.8); ax.set_axisbelow(True)
        for s in ('top', 'right'):
            ax.spines[s].set_visible(False)
        for s in ('left', 'bottom'):
            ax.spines[s].set_color(GRID)
        ax.tick_params(colors=INK2)
        ax.plot(code, [r[key] for r in rows], color=SERIES[0], linewidth=2, marker='o', markersize=4)
        if logy:
            ax.set_yscale('log')
        ax.set_ylabel(ylabel, color=INK2)
    axes[0].set_title(f'Bias sweep (DAC on BIAS_SEL) - {label}', color=INK, fontsize=11, loc='left')
    axes[-1].set_xlabel('DAC code (0-4095 = 0-3.3 V bias)', color=INK2)
    save(fig, path)


def run_gain(run):
    """A run's absolute 1 kHz gain (from its sweep), or None."""
    return json.loads((run / 'summary.json').read_text()).get('sweep', {}).get('gain_1k_db')


def plot_compare(runs, stem, absolute=False):
    """Overlay responses and noise spectra of earlier runs (whichever each run has). Returns saved paths.
    By default responses are relative to each run's 1 kHz gain and noise is relative to the signal
    (noise minus that gain), so runs with different gains compare fairly; absolute=True plots raw values.
    Runs are ordered by folder name (= date-time): the newest gets the first colour, is drawn on top,
    and heads the legend."""
    if len(runs) > len(SERIES):
        raise SystemExit(f'compare at most {len(SERIES)} runs at a time (colours stay distinct)')
    runs = sorted(runs, key=lambda r: r.name, reverse=True)
    saved = []
    response_label = 'Gain (dB re loopback)' if absolute else 'Gain relative to 1 kHz (dB)'
    noise_label = 'Noise density (dBFS/Hz)' if absolute else 'Noise relative to signal (dB/Hz)'
    charts = [('response.csv', 2, 'Frequency response - comparison', response_label, '_response.png'),
              ('noise_psd.csv', 1, 'Noise spectrum - comparison', noise_label, '_noise.png')]
    for filename, column, title, ylabel, suffix in charts:
        have = [r for r in runs if (r / filename).exists()]
        if filename == 'noise_psd.csv' and not absolute:
            skipped = [r.name for r in have if run_gain(r) is None]
            if skipped:
                print(f"  (noise relative to signal needs a sweep in the same run - skipping {', '.join(skipped)})")
            have = [r for r in have if run_gain(r) is not None]
        if not have:
            continue
        fig, ax = styled_axes(title, 'Frequency (Hz)', ylabel)
        for run in reversed(have):          # oldest first, so the newest is drawn on top
            rows = np.loadtxt(run / filename, delimiter=',', skiprows=1)
            rows = rows[(rows[:, 0] >= 20) & (rows[:, 0] <= 20000)]
            y = rows[:, column]
            if filename == 'response.csv' and not absolute:
                y = y - np.interp(1000, rows[:, 0], y)
            if filename == 'noise_psd.csv' and not absolute:
                y = y - run_gain(run)
            ax.plot(rows[:, 0], y, color=SERIES[runs.index(run)], linewidth=1.5 if column == 1 else 2,
                    label=run.name)
        ax.set_xlim(20, 20000)
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles[::-1], labels[::-1], frameon=False, fontsize=9, labelcolor=INK)   # newest first
        path = Path(str(stem) + suffix)
        save(fig, path)
        saved.append(path)

    # Distortion vs drive level (from each run's "levels" ramp), clipped points left out
    with_levels = [r for r in runs if json.loads((r / 'summary.json').read_text()).get('levels')]
    if with_levels:
        fig, axes = plt.subplots(2, 1, figsize=(8, 6.5), dpi=150, sharex=True)
        fig.patch.set_facecolor(SURFACE)
        for ax, key, ylabel in zip(axes, ('thd_pct', 'thd_n_pct'), ('THD, harmonics only (%)', 'THD+N (%)')):
            ax.set_facecolor(SURFACE); ax.grid(True, color=GRID, linewidth=0.8); ax.set_axisbelow(True)
            for s in ('top', 'right'):
                ax.spines[s].set_visible(False)
            for s in ('left', 'bottom'):
                ax.spines[s].set_color(GRID)
            ax.tick_params(colors=INK2)
            for run in reversed(with_levels):    # oldest first, so the newest is drawn on top
                rows = [r for r in json.loads((run / 'summary.json').read_text())['levels'] if not r.get('input_clipped')]
                ax.plot([r['level_dbfs'] for r in rows], [r[key] for r in rows], color=SERIES[runs.index(run)],
                        linewidth=2, marker='o', markersize=3, label=run.name)
            ax.set_yscale('log')
            ax.set_ylabel(ylabel, color=INK2)
        axes[0].set_title('Distortion vs drive at 1 kHz - comparison', color=INK, fontsize=11, loc='left')
        handles, labels = axes[0].get_legend_handles_labels()
        axes[0].legend(handles[::-1], labels[::-1], frameon=False, fontsize=8, labelcolor=INK)   # newest first
        axes[-1].set_xlabel('Drive level sent to Out (dBFS peak)', color=INK2)
        path = Path(str(stem) + '_distortion.png')
        save(fig, path)
        saved.append(path)
    return saved


# ---- Saving ------------------------------------------------------------------------------------------

def public(d):
    return {k: v for k, v in d.items() if not k.startswith('_')}


def write_csv(path, header, rows):
    with open(path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def save_wav(path, fs, x):
    from scipy.io import wavfile
    wavfile.write(path, fs, x.astype('float32'))


def replot(run):
    """Redraw a run's plots from its saved CSV/JSON (no measuring)."""
    summary = json.loads((run / 'summary.json').read_text())
    label = summary.get('label', run.name)
    if 'sweep' in summary and (run / 'response.csv').exists():
        rows = np.loadtxt(run / 'response.csv', delimiter=',', skiprows=1)
        plot_response(dict(summary['sweep'], _freqs=rows[:, 0], _mag=rows[:, 1], _smooth=rows[:, 2]),
                      run / 'response.png', label)
    if 'noise' in summary and (run / 'noise_psd.csv').exists():
        rows = np.loadtxt(run / 'noise_psd.csv', delimiter=',', skiprows=1)
        res = dict(summary['noise'], _freqs=rows[:, 0], _psd=10 ** (rows[:, 1] / 10))
        if (run / 'noise_psd_monitor.csv').exists():
            res['_psd_monitor'] = 10 ** (np.loadtxt(run / 'noise_psd_monitor.csv', delimiter=',', skiprows=1)[:, 1] / 10)
        if (run / 'transfer_monitor.csv').exists():
            t = np.loadtxt(run / 'transfer_monitor.csv', delimiter=',', skiprows=1)
            res['_transfer_db'] = np.interp(rows[:, 0], t[:, 0], t[:, 1])
        plot_noise(res, run / 'noise.png', label)
    if 'levels' in summary:
        plot_levels(summary['levels'], run / 'levels.png', label)


def reanalyse(run):
    """Recompute a run's frequency response from its saved sweep recording with the current analysis.
    Rewrites response.csv, response.png and summary.json's sweep numbers; keeps the first set of
    old numbers under sweep.before_reanalysis. Returns (old, new) sweep summaries, or None if no recording."""
    from scipy.io import wavfile
    summary = json.loads((run / 'summary.json').read_text())
    s = summary.get('sweep')
    if not s or not (run / 'sweep_recorded.wav').exists():
        return None
    fs, rec = wavfile.read(run / 'sweep_recorded.wav')
    rec = rec.astype(float)
    if rec.ndim > 1:
        rec = rec[:, 0]
    res = analyse_sweep(rec, fs, s['level_dbfs'], s['f1'], s['f2'], s['secs'])
    write_csv(run / 'response.csv', ['freq_hz', 'gain_db', 'gain_db_smoothed'],
              zip(np.round(res['_freqs'], 2), np.round(res['_mag'], 2), np.round(res['_smooth'], 2)))
    keys = ('gain_1k_db', 'minus3db_low_hz', 'minus3db_high_hz', 'latency_ms')
    old = s.get('before_reanalysis', {k: s.get(k) for k in keys})
    summary['sweep'] = dict(public(res), before_reanalysis=old,
                            reanalysed=datetime.date.today().isoformat())
    (run / 'summary.json').write_text(json.dumps(summary, indent=2))
    plot_response(res, run / 'response.png', summary.get('label', run.name))
    return old, public(res)


def run_dir(label):
    stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    d = RUNS / f'{stamp}_{label}'
    d.mkdir(parents=True, exist_ok=True)
    return d


def do_sweep(rig, args, out, summary):
    res = measure_sweep(rig, level_db=args.level, secs=args.sweep_secs)
    write_csv(out / 'response.csv', ['freq_hz', 'gain_db', 'gain_db_smoothed'],
              zip(np.round(res['_freqs'], 2), np.round(res['_mag'], 2), np.round(res['_smooth'], 2)))
    save_wav(out / 'sweep_recorded.wav', rig.fs, res['_rec'])
    plot_response(res, out / 'response.png', args.label)
    summary['sweep'] = public(res)
    print(f"sweep: 1 kHz gain {res['gain_1k_db']:+.1f} dB, −3 dB {res['minus3db_low_hz']} Hz – "
          f"{res['minus3db_high_hz']} Hz, latency {res['latency_ms']} ms")


def do_noise(rig, args, out, summary):
    transfer = measure_transfer(rig, args.monitor, level_db=args.level, secs=args.sweep_secs) if args.monitor else None
    res = measure_noise(rig, secs=args.noise_secs, monitor=args.monitor)
    res['in_ch'] = rig.in_ch
    write_csv(out / 'noise_psd.csv', ['freq_hz', 'psd_dbfs_per_hz'],
              zip(res['_freqs'], np.round(10 * np.log10(res['_psd'] + 1e-30), 2)))
    save_wav(out / 'noise_recorded.wav', rig.fs, res['_rec'])
    if args.monitor:
        write_csv(out / 'noise_psd_monitor.csv', ['freq_hz', 'psd_dbfs_per_hz'],
                  zip(res['_freqs'], np.round(10 * np.log10(res['_psd_monitor'] + 1e-30), 2)))
        save_wav(out / 'noise_recorded_monitor.wav', rig.fs, res['_rec_monitor'])
        tf, tdb = transfer
        write_csv(out / 'transfer_monitor.csv', ['freq_hz', 'in_over_monitor_db'], zip(np.round(tf, 2), np.round(tdb, 2)))
        res['_transfer_db'] = np.interp(res['_freqs'], tf, tdb)
        # The monitor's noise as it would appear at the photosensor input: total and the 50 Hz line
        f, df = res['_freqs'], res['_freqs'][1] - res['_freqs'][0]
        referred = res['_psd_monitor'] * 10 ** (res['_transfer_db'] / 10)
        band, near50 = (f >= 20) & (f <= 20000), (f >= 48) & (f <= 52)
        res['monitor_transfer_1k_db'] = round(float(np.interp(1000, tf, tdb)), 1)
        res['monitor_referred_rms_dbfs'] = round(float(10 * np.log10(referred[band].sum() * df)), 1)
        res['monitor_referred_50hz_dbfs'] = round(float(10 * np.log10(referred[near50].sum() * df)), 1)
    plot_noise(res, out / 'noise.png', args.label)
    summary['noise'] = public(res)
    fmt = lambda s: f"{s['rms_dbfs_20_20k']} dBFS (20 Hz–20 kHz), {s['rms_dbfs_a_weighted']} dBFS(A); peaks " + \
        ', '.join(f"{p['hz']:.0f} Hz (+{p['above_floor_db']:.0f} dB)" for p in s['peaks'])
    print(f"noise In {rig.in_ch}: {fmt(res)}")
    if args.monitor:
        print(f"noise In {args.monitor} (monitor): {fmt(res['monitor'])}")
        print(f"  referred to In {rig.in_ch} (transfer {res['monitor_transfer_1k_db']:+.1f} dB at 1 kHz): "
              f"{res['monitor_referred_rms_dbfs']} dBFS total, 50 Hz {res['monitor_referred_50hz_dbfs']} dBFS "
              f"(In {rig.in_ch} itself: {res['rms_dbfs_20_20k']}, 50 Hz {res['hum_dbfs']['50Hz']})")


def do_tones(rig, args, out, summary):
    rows = measure_tones(rig, level_db=args.level)
    write_csv(out / 'tones.csv', ['f0', 'level_dbfs', 'fundamental_dbfs', 'thd_pct', 'thd_n_pct', 'snr_db', 'h2_dbc', 'h3_dbc'],
              [[r['f0'], r['level_dbfs'], r['fundamental_dbfs'], r['thd_pct'], r['thd_n_pct'], r['snr_db'],
                r['harmonics_dbc'][0], r['harmonics_dbc'][1]] for r in rows])
    summary['tones'] = rows
    for r in rows:
        print(f"tone {r['f0']} Hz: back at {r['fundamental_dbfs']} dBFS, THD {r['thd_pct']}%, "
              f"THD+N {r['thd_n_pct']}%, SNR {r['snr_db']} dB")


def do_levels(rig, args, out, summary):
    rows = measure_levels(rig, hi=args.max_level)
    write_csv(out / 'levels.csv', ['level_dbfs', 'fundamental_dbfs', 'thd_pct', 'thd_n_pct', 'snr_db'],
              [[r['level_dbfs'], r['fundamental_dbfs'], r['thd_pct'], r['thd_n_pct'], r['snr_db']] for r in rows])
    plot_levels(rows, out / 'levels.png', args.label)
    summary['levels'] = rows
    best = min(rows, key=lambda r: r['thd_n_pct'])
    print(f"levels: lowest THD+N {best['thd_n_pct']}% at {best['level_dbfs']} dBFS drive")


def summarise(runs):
    """One row of key numbers per run (whatever each run measured). Returns (header, rows)."""
    header = ['run', 'bias', 'gain_1k_db', 'f_low_hz', 'f_high_hz', 'noise_dbfs', 'noise_a_dbfs',
              'noise_re_signal_db', 'hum50_dbfs', 'thd_1k_pct', 'drive_dbfs', 'best_thd_n_pct']
    rows = []
    for run in runs:
        s = json.loads((run / 'summary.json').read_text())
        sweep, noise = s.get('sweep', {}), s.get('noise', {})
        tone = next((t for t in s.get('tones', []) if t['f0'] == 1000), {})
        levels = s.get('levels', [])
        gain = sweep.get('gain_1k_db')
        rows.append([run.name, s.get('bias_code', 'trimmer'), gain, sweep.get('minus3db_low_hz'), sweep.get('minus3db_high_hz'),
                     noise.get('rms_dbfs_20_20k'), noise.get('rms_dbfs_a_weighted'),
                     round(noise['rms_dbfs_20_20k'] - gain, 1) if noise and gain is not None else None,
                     noise.get('hum_dbfs', {}).get('50Hz'), tone.get('thd_pct'), tone.get('level_dbfs'),
                     min((r['thd_n_pct'] for r in levels if not r.get('input_clipped')), default=None)])
    return header, rows


def markdown_table(header, rows):
    fmt = lambda v: '' if v is None else str(v)
    lines = ['| ' + ' | '.join(header) + ' |', '|' + '---|' * len(header)]
    lines += ['| ' + ' | '.join(fmt(v) for v in r) + ' |' for r in rows]
    return '\n'.join(lines)


def do_bias_sweep(rig, args, out, summary, dac):
    codes = list(range(args.bias_from, args.bias_to + 1, args.bias_step))
    rows = measure_bias_sweep(rig, dac, codes, level_db=args.level)
    write_csv(out / 'bias_sweep.csv', list(rows[0].keys()), [list(r.values()) for r in rows])
    plot_bias_sweep(rows, out / 'bias_sweep.png', args.label)
    summary['bias_sweep'] = rows
    best = min(rows, key=lambda r: r['thd_pct'])
    print(f"bias sweep: lowest THD {best['thd_pct']}% at code {best['code']} ({best['dac_volts']} V)")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('command', choices=['devices', 'sweep', 'noise', 'tones', 'levels', 'all', 'compare', 'replot',
                                       'biassweep', 'summarise', 'reanalyse'])
    p.add_argument('runs', nargs='*', help='run folders for "compare" / "replot" / "summarise"')
    p.add_argument('--absolute', action='store_true', help='compare: plot absolute gain instead of relative to 1 kHz')
    p.add_argument('--label', default='link', help='name added to the run folder')
    p.add_argument('--notes', default='', help='free text saved in summary.json (bias setting, distance...)')
    p.add_argument('--device', default=Rig.device)
    p.add_argument('--out', type=int, default=Rig.out_ch, help='output channel to the LED driver (1-based)')
    p.add_argument('--in', dest='in_ch', type=int, default=Rig.in_ch, help='input channel from the photosensor (1-based)')
    p.add_argument('--fs', type=int, default=Rig.fs)
    p.add_argument('--level', type=float, default=-20, help='sweep / tone level, dBFS peak')
    p.add_argument('--max-level', type=float, default=0, help='highest drive for "levels", dBFS peak')
    p.add_argument('--sweep-secs', type=float, default=8.0)
    p.add_argument('--noise-secs', type=float, default=10.0)
    p.add_argument('--monitor', type=int, default=None,
                   help='noise: also record this input at the same time (e.g. 2 = R13, the LED current), after a '
                        'sweep on both that refers its noise to the photosensor input')
    p.add_argument('--dac', default=None, help='serial port of the board running dac_test ("auto" to find it)')
    p.add_argument('--bias', type=int, default=None, help='with --dac: set this DAC code before measuring')
    p.add_argument('--bias-from', type=int, default=100)
    p.add_argument('--bias-to', type=int, default=2200, help='biassweep top code (~2200 = V1 limit of the current op-amp)')
    p.add_argument('--bias-step', type=int, default=150)
    args = p.parse_intermixed_args()   # lets options and run folders come in any order

    if args.command == 'devices':
        print(sd.query_devices())
        return
    if args.command == 'compare':
        runs = [Path(r) for r in args.runs]
        stem = RUNS / f"compare_{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
        for path in plot_compare(runs, stem, absolute=args.absolute):
            print(f'saved {path}')
        return
    if args.command == 'replot':
        for run in args.runs:
            replot(Path(run))
            print(f'replotted {run}')
        return
    if args.command == 'reanalyse':
        for run in args.runs:
            r = reanalyse(Path(run))
            if r is None:
                print(f'{run}: no sweep recording - skipped')
                continue
            old, new = r
            print(f"{Path(run).name}: 1 kHz gain {old['gain_1k_db']} → {new['gain_1k_db']} dB, "
                  f"−3 dB {old['minus3db_low_hz']}–{old['minus3db_high_hz']} → "
                  f"{new['minus3db_low_hz']}–{new['minus3db_high_hz']} Hz")
        return
    if args.command == 'summarise':
        header, rows = summarise([Path(r) for r in args.runs])
        stem = RUNS / f"summary_{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
        write_csv(Path(str(stem) + '.csv'), header, rows)
        Path(str(stem) + '.md').write_text(markdown_table(header, rows) + '\n')
        print(markdown_table(header, rows))
        print(f'saved {stem}.csv / .md')
        return

    rig = Rig(args.device, args.out, args.in_ch, args.fs)
    if args.command == 'biassweep' and not args.dac:
        raise SystemExit('biassweep needs --dac (e.g. --dac auto)')
    dac = Dac(args.dac) if args.dac else None
    out = run_dir(args.label)
    summary = {'rig': asdict(rig), 'label': args.label, 'notes': args.notes,
               'time': datetime.datetime.now().isoformat(timespec='seconds')}
    try:
        if dac and args.bias is not None:
            dac.set(args.bias)
            summary['bias_code'] = args.bias
            print(f'bias set to DAC code {args.bias} ({args.bias / 4095 * 3.3:.3f} V)')
        if args.command == 'biassweep':
            do_bias_sweep(rig, args, out, summary, dac)
        else:
            steps = {'sweep': [do_sweep], 'noise': [do_noise], 'tones': [do_tones], 'levels': [do_levels],
                     'all': [do_sweep, do_noise, do_tones, do_levels]}[args.command]
            for step in steps:
                step(rig, args, out, summary)
    finally:
        if dac:
            dac.close()
    with open(out / 'summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    print(f'saved {out}')


if __name__ == '__main__':
    main()
