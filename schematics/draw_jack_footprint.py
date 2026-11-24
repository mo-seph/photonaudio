"""Lumberg 1503 09 (3.5 mm stereo jack, 2 break contacts) - footprint reference, top (component) side view.
From the Lumberg data sheet (01/2018) 'printed circuit board layout, solder side view', mirrored to the top side.
Origin = pin 1, same as the Ultra Librarian part, so its pad coordinates can be checked directly.
Five plated slots 0.8 (+0.1) x 1.5 (+0.1) mm for 1.3 mm-wide solder tabs. Drawn here at 0.9 x 1.6 mm with a
0.4 mm annular ring (copper 1.7 x 2.4 mm).
Run: python draw_jack_footprint.py -> jack_1503_09_footprint.png"""
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

SLOT_W, SLOT_L, RING = 0.9, 1.6, 0.4
# pin: (x, y, orientation of the slot's long axis, J1 net, J_LED net)
# Numbering per the data sheet contact diagram (confirmed by Dave 2026-11-05): 2 = tip, 3 = ring, 4 = tip break,
# 5 = ring break. The Ultra Librarian symbol had tip and ring swapped.
PINS = {
    1: (0.00, 0.0, 'x', 'sleeve -> SLEEVE', 'sleeve -> U3 C'),
    2: (-4.55, -3.3, 'y', 'tip -> C8', 'tip -> R12'),
    3: (5.05, -7.8, 'y', 'ring -> C7', 'n.c.'),
    4: (-4.00, -11.0, 'x', 'tip break -> SLEEVE', 'n.c.'),
    5: (2.65, -6.4, 'y', 'ring break -> SLEEVE', 'n.c.'),
}
INK, MUTED, CU, BG = '#1f2328', '#6b7280', '#c2410c', '#fcfcfb'


def stadium(ax, x, y, w, h, **kw):
    """Rounded slot (stadium) of overall size w x h centred on (x, y)."""
    r = min(w, h) / 2
    ax.add_patch(FancyBboxPatch((x - w / 2 + r, y - h / 2 + r), w - 2 * r, h - 2 * r,
                                boxstyle=f'round,pad={r}', **kw))


fig, ax = plt.subplots(figsize=(7.2, 8.6), dpi=150)
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)

# body 11.5 x 14.1 (6 to +x, 5.5 to -x of the jack axis), bushing ø6 x 3.5 in front of it
ax.add_patch(Rectangle((-5.5, 2.1 - 14.1), 11.5, 14.1, fill=False, ec=MUTED, lw=1.0, ls='--'))
ax.add_patch(Rectangle((-3.0, 2.1), 6.0, 3.5, fill=False, ec=MUTED, lw=1.0, ls='--'))
ax.plot([0, 0], [-12.6, 6.4], color=MUTED, lw=0.6, ls='-.')
ax.text(0, 6.0, 'bushing ø6 (axis on pin 1)', ha='center', va='bottom', fontsize=8, color=MUTED)
ax.text(-5.3, 1.75, 'body front edge\n(y = +2.1)', ha='left', va='top', fontsize=7.5, color=MUTED)
ax.text(6.2, -12.0, 'body 11.5 x 14.1\nx = -5.5 ... +6.0', ha='left', va='bottom', fontsize=7.5, color=MUTED)

for n, (x, y, axis, j1, jled) in PINS.items():
    w, h = (SLOT_L, SLOT_W) if axis == 'x' else (SLOT_W, SLOT_L)
    stadium(ax, x, y, w + 2 * RING, h + 2 * RING, fc=CU, ec='none', alpha=0.85)
    stadium(ax, x, y, w, h, fc=BG, ec=INK, lw=0.8)
    right = n != 5          # pin 5's label goes left, clear of pin 3
    lx = x + (1.4 if right else -1.4)
    ha = 'left' if right else 'right'
    ax.text(lx, y, f'{n}', ha=ha, va='center', fontsize=12, weight='bold', color=INK)
    ax.text(lx + (0.75 if right else -0.75), y,
            f'({x:+.2f}, {y:+.1f})  slot along {axis}\nJ1: {j1}\nJ_LED: {jled}',
            ha=ha, va='center', fontsize=7.2, color=INK, linespacing=1.25)

ax.set_xlim(-11.5, 13.5)
ax.set_ylim(-16.8, 7.0)
ax.set_aspect('equal')
ax.set_xticks(range(-10, 13, 2))
ax.set_yticks(range(-16, 8, 2))
ax.tick_params(labelsize=7, colors=MUTED)
ax.grid(color='#e5e7eb', lw=0.5)
ax.set_axisbelow(True)
for s in ax.spines.values():
    s.set_color('#d1d5db')
ax.set_xlabel('x (mm), top view, origin = pin 1', fontsize=8, color=MUTED)
ax.set_title('Lumberg 1503 09 footprint, component side', fontsize=11, color=INK, loc='left')
ax.text(-11.2, -14.2,
        f'5 plated slots {SLOT_W} x {SLOT_L} mm (data sheet 0.8 x 1.5, +0.1/-0), copper {SLOT_W + 2 * RING:.1f} x '
        f'{SLOT_L + 2 * RING:.1f} mm, top + bottom\n'
        'Pin 2 is on the -x side seen from the top: the data sheet layout is a solder-side view (mirrored).\n'
        'Tolerance on pin positions ±0.1 mm. Board edge can sit at the body front (y = +2.1) or under the bushing.',
        ha='left', va='top', fontsize=7.2, color=INK, linespacing=1.35)

fig.tight_layout()
fig.savefig('jack_1503_09_footprint.png', facecolor=BG)
