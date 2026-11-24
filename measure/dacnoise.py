"""DAC update noise (2026-11-03): does writing the bias DAC add noise to the link?

Records the noise (In 1, plus a monitor input such as R13 on In 2) four ways at one bias code,
driving the dac_test firmware from here over USB serial:
  steady    no writes
  usb       "a" with no value at --rate Hz: USB serial traffic and replies, no I2C
  rewrite   the same code at --rate Hz: I2C traffic, the DAC output doesn't change
  ramp      a slow triangle, --code ± --span over --period s, written at --rate Hz:
            the output steps one code at a time, like a slow LFO on the bias
The update timing comes from this computer, so it jitters by a millisecond or so (the XIAO firmware
will be steadier). Saves runs/<stamp>_<label>/: noise_psd_<case>.csv (+ _monitor), summary.json,
dac_noise.png.

Run:  ~/.virtualenvs/aotest/bin/python dacnoise.py --dac /dev/cu.SLAB_USBtoUART --code 450 --label dacnoise_450
"""
import argparse
import json
import threading
import time

import numpy as np
import matplotlib.pyplot as plt

from linkmeasure import Rig, Dac, measure_noise, run_dir, write_csv, SURFACE, INK, INK2
from noise_history import display, style, log_freq_axis, BEFORE

COLOURS = {'steady': BEFORE, 'usb': '#1baf7a', 'rewrite': '#2a78d6', 'ramp': '#eb6834'}
BANDS = [(20, 20000), (20, 300), (300, 2500), (2500, 20000)]


class Writer:
    """Sends one line per tick at a steady rate on a thread, and drains the firmware's replies."""

    def __init__(self, port, line_for, rate):
        self.port, self.line_for, self.rate = port, line_for, rate
        self.stop_event = threading.Event()
        self.sent = 0

    def run(self):
        t0 = time.perf_counter()
        while not self.stop_event.is_set():
            self.port.write(self.line_for(time.perf_counter() - t0).encode())
            self.sent += 1
            if self.port.in_waiting:
                self.port.read(self.port.in_waiting)
            next_tick = t0 + self.sent / self.rate
            time.sleep(max(0.0, next_tick - time.perf_counter()))
        self.elapsed = time.perf_counter() - t0

    def __enter__(self):
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()
        return self

    def __exit__(self, *exc):
        self.stop_event.set()
        self.thread.join()


def band_db(freqs, psd, lo, hi):
    band = (freqs >= lo) & (freqs <= hi)
    return round(float(10 * np.log10(psd[band].sum() * (freqs[1] - freqs[0]))), 1)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--dac', required=True)
    ap.add_argument('--code', type=int, default=450)
    ap.add_argument('--span', type=int, default=60, help='ramp: ± this many codes around --code')
    ap.add_argument('--period', type=float, default=3.0, help='ramp: triangle period (s)')
    ap.add_argument('--rate', type=float, default=500, help='DAC writes per second')
    ap.add_argument('--secs', type=float, default=10.0)
    ap.add_argument('--monitor', type=int, default=2)
    ap.add_argument('--ref', choices=('vdd', 'int'), default='vdd',
                    help='DAC reference: vdd (0.8 mV steps) or int (internal 2.048 V, 0.5 mV steps)')
    ap.add_argument('--label', default='dacnoise')
    ap.add_argument('--notes', default='')
    args = ap.parse_args()

    rig = Rig()
    dac = Dac(args.dac)
    dac.serial.write(f'ref {args.ref}\n'.encode())
    deadline = time.time() + 6
    while not dac.serial.readline().decode(errors='replace').startswith('ref ='):
        if time.time() > deadline:
            raise SystemExit(f'DAC did not confirm "ref {args.ref}" - is the updated dac_test firmware flashed?')
    dac.set(args.code)

    def ramp(t):
        phase = (t / args.period) % 1.0
        tri = 4 * phase - 1 if phase < 0.5 else 3 - 4 * phase          # −1 → 1 → −1
        return f'a {int(round(args.code + args.span * tri))}\n'

    cases = [('steady', None), ('usb', lambda t: 'a\n'), ('rewrite', lambda t: f'a {args.code}\n'), ('ramp', ramp)]
    out = run_dir(args.label)
    summary = {'label': args.label, 'notes': args.notes, 'time': time.strftime('%Y-%m-%dT%H:%M:%S'),
               'code': args.code, 'ref': args.ref, 'span': args.span, 'period_s': args.period, 'rate_hz': args.rate,
               'ramp_steps_per_s': 4 * args.span / args.period, 'cases': {}}
    results = {}
    for name, line_for in cases:
        if line_for is None:
            res = measure_noise(rig, args.secs, args.monitor)
            achieved = 0.0
        else:
            with Writer(dac.serial, line_for, args.rate) as w:
                time.sleep(0.5)
                res = measure_noise(rig, args.secs, args.monitor)
            achieved = w.sent / w.elapsed
            time.sleep(0.2)
            dac.serial.reset_input_buffer()
            dac.set(args.code)
        results[name] = res
        f = res['_freqs']
        for suffix, psd in (('', res['_psd']), ('_monitor', res['_psd_monitor'])):
            write_csv(out / f'noise_psd_{name}{suffix}.csv', ['freq_hz', 'psd_dbfs_per_hz'],
                      [[round(float(a), 2), round(float(b), 2)] for a, b in zip(f, 10 * np.log10(psd + 1e-30))])
        summary['cases'][name] = {
            'writes_per_s': round(achieved, 1),
            'in1_bands_dbfs': {f'{lo}-{hi}': band_db(f, res['_psd'], lo, hi) for lo, hi in BANDS},
            'monitor_bands_dbfs': {f'{lo}-{hi}': band_db(f, res['_psd_monitor'], lo, hi) for lo, hi in BANDS},
            'in1_peaks': res['peaks'], 'monitor_peaks': res['monitor']['peaks']}
    dac.close()
    (out / 'summary.json').write_text(json.dumps(summary, indent=2))

    print(f"{'case':8s} {'writes/s':>8s}   In 1 dBFS: total / 20-300 / 300-2.5k / 2.5k-20k      In {args.monitor} dBFS: same bands")
    for name, c in summary['cases'].items():
        a, m = c['in1_bands_dbfs'].values(), c['monitor_bands_dbfs'].values()
        print(f"{name:8s} {c['writes_per_s']:8.0f}   " + ' / '.join(f'{v:6.1f}' for v in a)
              + '      ' + ' / '.join(f'{v:6.1f}' for v in m))
        print('         peaks In 1: ' + ', '.join(f"{p['hz']:.0f} Hz (+{p['above_floor_db']:.0f})" for p in c['in1_peaks']))

    fig, axes = plt.subplots(1, 2, figsize=(14, 4.8), dpi=150, sharex=True)
    fig.patch.set_facecolor(SURFACE)
    for ax, key, title in ((axes[0], '_psd', 'Photosensor (In 1)'),
                           (axes[1], '_psd_monitor', f'LED current (In {args.monitor} across R13)')):
        style(ax); log_freq_axis(ax)
        for name, res in results.items():
            curve = display({'freqs': res['_freqs'], 'psd_db': 10 * np.log10(res[key] + 1e-30), 'gain': 0.0})
            ax.plot(*curve, color=COLOURS[name], linewidth=1.3 if name == 'steady' else 1, label=name)
        ax.set_title(title, color=INK, fontsize=11, loc='left')
        ax.set_xlabel('Frequency (Hz)', color=INK2)
        ax.set_ylabel('Noise density (dBFS/Hz)', color=INK2)
        ax.legend(frameon=False, fontsize=8.5, labelcolor=INK, loc='lower left')
    fig.suptitle(f'DAC update noise at code {args.code} ({args.ref} ref): {args.rate:.0f} writes/s; ramp ±{args.span} codes over '
                 f'{args.period:g} s ({summary["ramp_steps_per_s"]:.0f} steps/s)', color=INK, fontsize=12, x=0.01, ha='left')
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(out / 'dac_noise.png', facecolor=SURFACE)
    plt.close(fig)
    print(f'saved {out}')


if __name__ == '__main__':
    main()
