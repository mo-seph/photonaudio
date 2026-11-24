"""Noise history (2026-11-03): how each change to the link moved its noise floor and changed its shape.

Noise is plotted relative to the signal (noise minus each run's 1 kHz gain), so runs with different
optical gains compare fairly: a 0 dBFS drive at 1 kHz would sit at 0 dB. The housing runs with In 2
on R13 have no sweep of their own, so they borrow housing_250's gain (same housing, bias and supply;
their In 2 -> In 1 transfer at 1 kHz agrees within 0.5 dB, so the optical gain didn't move).

Run:  ~/.virtualenvs/aotest/bin/python noise_history.py
  -> runs/noise_history_spectra.png   one panel per change: before (grey) vs after (blue)
     runs/noise_history_bands.png     total and band noise at each stage
     runs/noise_history.md / .csv     the numbers
"""
import json

import numpy as np
import matplotlib.pyplot as plt

from linkmeasure import RUNS, SURFACE, INK, INK2, GRID, a_weighting_db, write_csv, markdown_table

BEFORE, AFTER = '#9a9893', '#2a78d6'
HOUSING_GAIN_RUN = '20261103-105453_housing_250'

# (run, short name, what changed to get here). Chronological; each step is one change (or one session).
STAGES = [
    ('20261024-121433_dac_all_500', 'Old op-amp, code 500',
     'Oct 24: counterfeit LM358-type, old 12 V adapter, boxed'),
    ('20261102-223002_c10_fitted', 'MCP6002 + C10, code 2048',
     'Genuine MCP6002, C9/C10: THD 0.5 → 0.07%. But at bias 2048\nthe pickup compresses (gain +9 → −2 dB), so noise rises'),
    ('20261102-224430_new_supply', 'New 12 V supply',
     'Old SMPS adapter swapped for another 12 V supply:\nits ~3.7 kHz burst tone goes (the new one bursts at 9.6 kHz)'),
    ('20261103-110608_housing_r13_250', 'Housing, code 250',
     'LED + pickup in the light-tight housing, LED much closer\n(optical gain +31 dB), bias 2048 → 250, laptop on charger'),
    ('20261103-112302_battery9v_r13_250', '9 V battery',
     '9 V PP3 in place of the 12 V SMPS (laptop still on charger):\nthe burst-mode line goes'),
    ('20261103-112627_battery9v_laptopbatt_r13_250', 'Laptop off charger',
     'Laptop on its own battery: no charger leakage current\nthrough the USB and audio grounds, so the hum goes'),
]
FLOOR_RUN = '20261103-110542_housing_r13_0'   # LED off: pickup + preamp only

BANDS = [('20 Hz–20 kHz', 20, 20000), ('20–300 Hz\n(mains comb)', 20, 300), ('300 Hz–2.5 kHz', 300, 2500),
         ('2.5–5 kHz\n(SMPS burst line)', 2500, 5000), ('5–20 kHz', 5000, 20000)]

# Features to point at in the spectra: (panel index, frequency, label, label offset in points, alignment)
FEATURES = [(1, 3675, 'old adapter\'s\nburst tone', (-40, 14), 'right'),
            (3, 3500, 'SMPS burst line\n(3.5 kHz)', (-40, 18), 'right'),
            (4, 50, '50 Hz comb\n(charger leakage)', (28, 4), 'left')]


def minus(text):
    """Typographic minus signs, to match the axis labels."""
    return text.replace('-', '−')


def load(name):
    run = RUNS / name
    s = json.loads((run / 'summary.json').read_text())
    rows = np.loadtxt(run / 'noise_psd.csv', delimiter=',', skiprows=1)
    gain = s.get('sweep', {}).get('gain_1k_db')
    borrowed = gain is None
    if borrowed:
        gain = json.loads((RUNS / HOUSING_GAIN_RUN / 'summary.json').read_text())['sweep']['gain_1k_db']
    return {'summary': s, 'freqs': rows[:, 0], 'psd_db': rows[:, 1], 'gain': gain, 'borrowed': borrowed}


def band_db(r, lo, hi, weighted=False):
    """Noise power in a band, relative to the signal (dB)."""
    f, p = r['freqs'], 10 ** (r['psd_db'] / 10)
    band = (f >= lo) & (f <= hi)
    w = 10 ** (a_weighting_db(f[band]) / 10) if weighted else 1
    return 10 * np.log10((p[band] * w).sum() * (f[1] - f[0])) - r['gain']


def display(r, per_octave=48, raw_below=140):
    """Spectrum for plotting: the 1 Hz bins as measured below raw_below (keeps the mains lines sharp),
    power-averaged over 1/per_octave-octave bins above it (tames the scatter of the 1 Hz bins)."""
    f, p = r['freqs'], 10 ** (r['psd_db'] / 10)
    low = (f >= 20) & (f < raw_below)
    edges = raw_below * 2 ** (np.arange(0, np.log2(20000 / raw_below) * per_octave + 1) / per_octave)
    c = np.concatenate([[0], np.cumsum(p)])
    lo, hi = np.searchsorted(f, edges[:-1]), np.searchsorted(f, edges[1:])
    hi = np.maximum(hi, lo + 1)
    centres = np.sqrt(edges[:-1] * edges[1:])
    x = np.concatenate([f[low], centres])
    y = np.concatenate([p[low], (c[hi] - c[lo]) / (hi - lo)])
    return x, 10 * np.log10(y) - r['gain']


def style(ax):
    ax.set_facecolor(SURFACE)
    ax.grid(True, which='major', color=GRID, linewidth=0.8); ax.set_axisbelow(True)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    for s in ('left', 'bottom'):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=INK2, labelsize=9)


def log_freq_axis(ax):
    ax.set_xscale('log')
    ax.set_xticks([20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000])
    ax.set_xticklabels(['20', '50', '100', '200', '500', '1k', '2k', '5k', '10k', '20k'])
    ax.set_xlim(20, 20000)


def plot_spectra(stages, floor, path):
    fig, axes = plt.subplots(2, 3, figsize=(14, 8.6), dpi=150, sharex=True)
    fig.patch.set_facecolor(SURFACE)
    axes = axes.ravel()
    curves = [display(st['data']) for st in stages]

    def panel(ax, title, subtitle, a, b, labels):
        style(ax); log_freq_axis(ax)
        ax.plot(*curves[a], color=BEFORE, linewidth=1, label=labels[0])
        ax.plot(*curves[b], color=AFTER, linewidth=1.2, label=labels[1])
        ta, tb = stages[a]['total'], stages[b]['total']
        ax.set_title(title, color=INK, fontsize=11, loc='left', pad=30)
        ax.text(0, 1.02, subtitle, transform=ax.transAxes, color=INK2, fontsize=8.5)
        ax.text(0.98, 0.97, minus(f"total {ta:.1f} → {tb:.1f} dB  ({tb - ta:+.1f})"), transform=ax.transAxes,
                ha='right', va='top', color=INK, fontsize=9.5)

    for i, ax in enumerate(axes[:5]):
        a, b = stages[i], stages[i + 1]
        panel(ax, f"{i + 1}. {b['name']}", b['change'], i, i + 1, (f"before: {a['name']}", f"after: {b['name']}"))
        ax.set_ylim(-142, -70)
        ax.legend(frameon=False, fontsize=8.5, labelcolor=INK, loc='lower left')
    for i, f0, text, offset, ha in FEATURES:
        x, y = curves[i]
        k = (x > f0 * 0.9) & (x < f0 * 1.1)
        axes[i].annotate(text, (x[k][y[k].argmax()], y[k].max()), xytext=offset, textcoords='offset points',
                         ha=ha, va='bottom', color=INK2, fontsize=8.5,
                         arrowprops=dict(arrowstyle='-', color=INK2, linewidth=0.8, shrinkA=0, shrinkB=2))

    # Start vs now, with the LED-off floor: needs its own (deeper) y range
    ax = axes[5]
    panel(ax, 'Start vs now', 'LED-off floor drawn at the housing\'s gain: everything\nabove it is carried by the light',
          0, -1, (f"start: {stages[0]['name']}", f"now: {stages[-1]['name']}"))
    ax.plot(*display(floor), color=INK, linewidth=0.9, linestyle=(0, (2, 2)), label='LED off: pickup + preamp floor')
    ax.set_ylim(-200, -70)   # room under the floor for the legend
    ax.legend(frameon=False, fontsize=8.5, labelcolor=INK, loc='lower left')

    for ax in axes[3:]:
        ax.set_xlabel('Frequency (Hz)', color=INK2)
    for ax in axes[::3]:
        ax.set_ylabel('Noise relative to signal (dB/Hz)', color=INK2)
    fig.suptitle('Link noise, output silent: what each change did', color=INK, fontsize=13, x=0.01, ha='left')
    fig.text(0.01, 0.005, 'Noise minus each run\'s 1 kHz gain, so 0 dB = a full-scale 1 kHz drive. 1 Hz bins below '
             '140 Hz, 1/48-octave power averages above. Totals are 20 Hz–20 kHz. Stages 4-6 use housing_250\'s gain. '
             'Start vs now has a deeper y scale.', color=INK2, fontsize=8.5)
    fig.tight_layout(rect=(0, 0.02, 1, 0.97), h_pad=3)
    fig.savefig(path, facecolor=SURFACE)
    plt.close(fig)


def plot_bands(stages, path):
    fig, axes = plt.subplots(1, len(BANDS), figsize=(14, 4.4), dpi=150, sharex=True, sharey=True)
    fig.patch.set_facecolor(SURFACE)
    y = np.arange(len(stages))[::-1]
    for j, (ax, (label, lo, hi)) in enumerate(zip(axes, BANDS)):
        style(ax)
        ax.grid(False, axis='y')
        v = [st['bands'][j] for st in stages]
        ax.plot(v, y, color=GRID, linewidth=1.5, zorder=1)
        ax.scatter(v, y, s=46, color=AFTER, edgecolor=SURFACE, linewidth=1.5, zorder=2)
        if j == 0:
            for vi, yi in zip(v, y):
                ax.text(vi + 1.5, yi, minus(f'{vi:.1f}'), va='center', color=INK, fontsize=8.5)
        ax.set_title(label, color=INK, fontsize=10, loc='left')
        ax.set_xlabel('dB re signal', color=INK2)
    lo = min(min(st['bands']) for st in stages)
    hi = max(max(st['bands']) for st in stages)
    axes[0].set_xlim(lo - 3, hi + 7)
    axes[0].set_yticks(y)
    axes[0].set_yticklabels([st['name'] for st in stages], color=INK)
    axes[0].set_ylim(-0.6, len(stages) - 0.4)
    fig.suptitle('Noise relative to signal at each stage, by band (further left = quieter; same dB scale in every panel)',
                 color=INK, fontsize=12, x=0.01, ha='left')
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(path, facecolor=SURFACE)
    plt.close(fig)


def main():
    stages = []
    for run, name, change in STAGES:
        r = load(run)
        bands = [round(band_db(r, lo, hi), 1) for _, lo, hi in BANDS]
        stages.append({'run': run, 'name': name, 'change': change, 'data': r, 'bands': bands, 'total': bands[0]})
    floor = load(FLOOR_RUN)

    header = ['stage', 'run', 'gain_1k_db', 'noise_dbfs', 'noise_re_signal_db', 'noise_a_re_signal_db',
              'snr_at_-30dbfs_drive_db', 'hum50_re_signal_db', '20_300hz_db', '300_2500hz_db', '2500_5000hz_db',
              '5k_20khz_db', 'thd_1k_pct']
    rows = []
    for st in stages:
        r, s = st['data'], st['data']['summary']
        gain = f"{r['gain']:.1f}" + (' *' if r['borrowed'] else '')
        # a −30 dBFS-peak 1 kHz drive is −33 dBFS rms and comes back at −33 + gain
        snr = -30 - 3.01 - st['total']
        tone = next((t for t in s.get('tones', []) if t['f0'] == 1000), {})
        rows.append([st['name'], st['run'], gain, s['noise']['rms_dbfs_20_20k'], st['total'],
                     round(band_db(r, 20, 20000, weighted=True), 1), round(snr, 1),
                     round(s['noise']['hum_dbfs']['50Hz'] - r['gain'], 1), *st['bands'][1:], tone.get('thd_pct')])
    write_csv(RUNS / 'noise_history.csv', header, rows)
    floor_re = band_db({**floor, 'gain': stages[-1]['data']['gain']}, 20, 20000)
    (RUNS / 'noise_history.md').write_text(
        '# Noise history\n\nAll noise figures in dB relative to the signal (noise minus the 1 kHz gain), 20 Hz-20 kHz '
        'unless a band is given. SNR and THD are for a -30 dBFS-peak 1 kHz drive.\n'
        '\\* gain borrowed from housing_250 (same housing, bias and supply; its THD at 1 kHz was 0.455%).\n\n'
        + markdown_table(header, rows)
        + f'\n\nLED off (pickup + preamp floor, {FLOOR_RUN}) at the housing gain: {floor_re:.1f} dB re signal.\n')
    plot_spectra(stages, floor, RUNS / 'noise_history_spectra.png')
    plot_bands(stages, RUNS / 'noise_history_bands.png')
    print((RUNS / 'noise_history.md').read_text())


if __name__ == '__main__':
    main()
