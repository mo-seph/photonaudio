"""Draw the Quad LED Driver board with parts highlighted and labelled.

draw(board, view, out, ...) renders one picture:
- the bare board (outline, holes, top copper under the mask, pads, silkscreen);
- `stage` parts in amber, `fitted` parts (earlier stages) as dark bodies,
  `dnf` parts crossed out in red;
- labels for `labels` (element names) placed clear of each other with leaders;
- probe markers with labels.
"""
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle, Circle, FancyBboxPatch
from matplotlib.collections import LineCollection, PatchCollection

C = dict(
    sub="#22433a", edge="#16302a", cu="#2b5446", pad="#c4c9cf", hole="#0b1411",
    silk="#e6ebe8", stage="#f0a43a", stage_edge="#ffcf7a", body="#2a2b2f",
    body_edge="#80858c", dnf="#e24b3f", probe="#35c2dc", label_bg="#fffaf1",
    label_fg="#1b1d1f", dim="#0d1a16",
)


def _poly(ax, pts, **kw):
    ax.add_patch(Polygon(pts, closed=True, **kw))


def _lines(ax, segs, color, lw_mm, ppm, z, alpha=1.0):
    """Line widths are in board mm; convert to points (dpi 100)."""
    if not segs:
        return
    lc = LineCollection([s for s, _ in segs], colors=color,
                        linewidths=[max(w, 0.05) * ppm * 0.72 for _, w in segs],
                        capstyle="round", joinstyle="round", zorder=z, alpha=alpha)
    ax.add_collection(lc)


def body_rect(e, shrink=0.0):
    x0, y0, x1, y1 = e["bbox"]
    return x0 + shrink, y0 + shrink, x1 - shrink, y1 - shrink


def pad_extent(e):
    xs = [q[0] for p in e["pads"] for q in p["poly"]]
    ys = [q[1] for p in e["pads"] for q in p["poly"]]
    return min(xs), min(ys), max(xs), max(ys)


def polarity(ax, e, ppm, color="#141414", z=30):
    """Mark orientation: diode cathode band, '+' on polarised caps, pin-1 dot on ICs."""
    names = {p["name"]: p for p in e["pads"]}
    fs = 1.9 * ppm * 0.72
    if "A" in names and "C" in names:
        a, c = names["A"], names["C"]
        ux, uy = a["x"] - c["x"], a["y"] - c["y"]
        L = math.hypot(ux, uy); ux, uy = ux / L, uy / L
        # band just inside the cathode pad, across the body
        bx, by = c["x"] + ux * 1.15, c["y"] + uy * 1.15
        px, py = -uy, ux
        half = 1.3
        ax.plot([bx - px * half, bx + px * half], [by - py * half, by + py * half],
                color=color, lw=0.55 * ppm * 0.72, solid_capstyle="butt", zorder=z)
    elif "+" in names:
        p = names["+"]
        q = names.get("-")
        dx, dy = (p["x"] - q["x"], p["y"] - q["y"]) if q else (1, 0)
        L = math.hypot(dx, dy) or 1
        ox, oy = dx / L * 0.0, dy / L * 0.0
        ax.text(p["x"] + ox, p["y"] + oy, "+", ha="center", va="center", fontsize=fs * 1.15,
                color=color, weight="bold", zorder=z)
    elif e["name"] == "C1":
        p = names["1"]
        ax.text(p["x"], p["y"], "+", ha="center", va="center", fontsize=fs * 1.15,
                color=color, weight="bold", zorder=z)
    elif e["name"].startswith("U") and "1" in names and len(e["pads"]) >= 8 \
            and not e["package"].startswith("XIAO"):
        p = names["1"]
        # dot between pad 1 and the body centre
        cx, cy = e["x"], e["y"]
        dx, dy = cx - p["x"], cy - p["y"]
        L = math.hypot(dx, dy)
        ax.add_patch(Circle((p["x"] + dx / L * 1.25, p["y"] + dy / L * 1.25), 0.32,
                            color=color, zorder=z))


def draw(B, view, out, ppm=20, stage=(), fitted=(), dnf=(), labels=None, probes=(),
         dim=True, title=None, label_mm=1.55, region=None, note=None):
    """labels: dict element -> list of lines. probes: list of (x, y, [lines])."""
    x0, y0, x1, y1 = view
    w, h = x1 - x0, y1 - y0
    fig = plt.figure(figsize=(w * ppm / 100, h * ppm / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect("equal"); ax.axis("off")
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#ffffff")

    bx0, by0, bx1, by1 = B.extent
    ax.add_patch(Rectangle((bx0, by0), bx1 - bx0, by1 - by0, fc=C["sub"], ec=C["edge"],
                           lw=0.6 * ppm * 0.72, zorder=1))
    _lines(ax, B.traces[1], C["cu"], 1, ppm, 2)
    for vx, vy, vd, vdia in B.vias:
        ax.add_patch(Circle((vx, vy), vdia / 2, color=C["cu"], zorder=2))
        ax.add_patch(Circle((vx, vy), vd / 2, color=C["hole"], zorder=3))
    for hx, hy, hd in B.holes:
        ax.add_patch(Circle((hx, hy), hd / 2, color="#ffffff", zorder=3))
        ax.add_patch(Circle((hx, hy), hd / 2, fill=False, ec=C["edge"], lw=1, zorder=3))
    for e in B.elements.values():
        for p in e["pads"]:
            _poly(ax, p["poly"], fc=C["pad"], ec="none", zorder=4)
            if p["kind"] == "pad":
                ax.add_patch(Circle((p["x"], p["y"]), p["drill"] / 2, color=C["hole"], zorder=5))
        _lines(ax, [s for s in e["silk"] if s[1] >= 0], C["silk"], 1, ppm, 4, alpha=0.75)
    for t in B.texts:
        _, ang = (t["rot"].count("M") > 0, float(t["rot"].split("R")[-1]) if "R" in t["rot"] else 0.0)
        ax.text(t["x"], t["y"], t["text"], fontsize=t["size"] * 1.25 * ppm * 0.72, color=C["silk"],
                rotation=ang, rotation_mode="anchor", ha="left", va="bottom", alpha=0.75,
                zorder=4, family="DejaVu Sans")

    if dim:
        ax.add_patch(Rectangle((x0 - 5, y0 - 5), w + 10, h + 10, fc=C["dim"], alpha=0.45, zorder=6))

    def redraw_pads(e, z):
        for p in e["pads"]:
            _poly(ax, p["poly"], fc=C["pad"], ec="none", zorder=z)
            if p["kind"] == "pad":
                ax.add_patch(Circle((p["x"], p["y"]), p["drill"] / 2, color=C["hole"], zorder=z + 0.1))

    for n in fitted:
        e = B.elements[n]
        rx0, ry0, rx1, ry1 = body_rect(e)
        redraw_pads(e, 7)
        ax.add_patch(FancyBboxPatch((rx0, ry0), rx1 - rx0, ry1 - ry0,
                                    boxstyle="round,pad=0,rounding_size=0.3",
                                    fc=C["body"], ec=C["body_edge"], lw=0.12 * ppm * 0.72,
                                    alpha=0.92, zorder=8))
        polarity(ax, e, ppm, color="#d8dadd", z=9)

    for n in stage:
        e = B.elements[n]
        rx0, ry0, rx1, ry1 = body_rect(e)
        ax.add_patch(FancyBboxPatch((rx0, ry0), rx1 - rx0, ry1 - ry0,
                                    boxstyle="round,pad=0.25,rounding_size=0.4",
                                    fc=C["stage"], ec=C["stage_edge"], lw=0.18 * ppm * 0.72,
                                    alpha=0.95, zorder=10))
        redraw_pads(e, 11)
        _lines(ax, [s for s in e["silk"] if s[1] >= 0], "#3b2a10", 1, ppm, 11.5, alpha=0.55)
        polarity(ax, e, ppm, z=12)

    for n in dnf:
        e = B.elements[n]
        rx0, ry0, rx1, ry1 = pad_extent(e)
        ax.add_patch(Rectangle((rx0 - 0.3, ry0 - 0.3), rx1 - rx0 + 0.6, ry1 - ry0 + 0.6, fill=False,
                               ec=C["dnf"], lw=0.2 * ppm * 0.72, ls=(0, (3, 2)), zorder=10))
        ax.plot([rx0, rx1], [ry0, ry1], color=C["dnf"], lw=0.2 * ppm * 0.72, zorder=10)
        ax.plot([rx0, rx1], [ry1, ry0], color=C["dnf"], lw=0.2 * ppm * 0.72, zorder=10)

    if region:
        rx0, ry0, rx1, ry1 = region
        ax.add_patch(Rectangle((rx0, ry0), rx1 - rx0, ry1 - ry0, fill=False, ec=C["probe"],
                               lw=0.35 * ppm * 0.72, ls=(0, (4, 2)), zorder=13))

    # ---- labels -------------------------------------------------------
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    inv = ax.transData.inverted()
    fs = label_mm * ppm * 0.72
    occupied = []
    for n in (labels or {}):
        for m in (n if isinstance(n, tuple) else (n,)):
            occupied.append(body_rect(B.elements[m]))
    for px, py, _ in probes:
        occupied.append((px - 0.9, py - 0.9, px + 0.9, py + 0.9))

    items = []
    for n, lines in (labels or {}).items():
        members = n if isinstance(n, tuple) else (n,)
        rects = [body_rect(B.elements[m]) for m in members]
        anchor = (min(r[0] for r in rects), min(r[1] for r in rects),
                  max(r[2] for r in rects), max(r[3] for r in rects))
        items.append(dict(anchor=anchor, lines=lines, kind="part", members=rects,
                          cx=(anchor[0] + anchor[2]) / 2, cy=(anchor[1] + anchor[3]) / 2))
    for px, py, lines in probes:
        a = (px - 0.9, py - 0.9, px + 0.9, py + 0.9)
        items.append(dict(anchor=a, lines=lines, kind="probe", members=[a], cx=px, cy=py))

    if items:
        gcx = sum(i["cx"] for i in items) / len(items)
    pad = 0.35  # label padding in mm

    def measure(lines, bold_first=True):
        t = ax.text(0, 0, "\n".join(lines), fontsize=fs, family="DejaVu Sans",
                    linespacing=1.15, zorder=-1)
        bb = t.get_window_extent(renderer=renderer)
        t.remove()
        (ax0, ay0), (ax1, ay1) = inv.transform([(bb.x0, bb.y0), (bb.x1, bb.y1)])
        return ax1 - ax0 + 2 * pad, ay1 - ay0 + 2 * pad

    def overlaps(r, rs, m=0.25):
        for q in rs:
            if r[0] < q[2] + m and r[2] > q[0] - m and r[1] < q[3] + m and r[3] > q[1] - m:
                return True
        return False

    # most crowded first: sort by number of items within 6 mm
    def crowd(i):
        return -sum(1 for j in items if abs(j["cx"] - i["cx"]) < 6 and abs(j["cy"] - i["cy"]) < 6)
    items.sort(key=crowd)

    placed = []
    for it in items:
        lw_, lh_ = measure(it["lines"])
        ax0_, ay0_, ax1_, ay1_ = it["anchor"]
        acx, acy = (ax0_ + ax1_) / 2, (ay0_ + ay1_) / 2
        left_first = it["cx"] < gcx
        best = None
        for k in range(0, 60):
            d = 0.3 + k * 0.5
            cands = []
            for s in (0, 1, -1, 2, -2, 3, -3):
                sy = s * (lh_ * 0.6)
                sx = s * (lw_ * 0.35)
                L = (ax0_ - d - lw_, acy - lh_ / 2 + sy, ax0_ - d, acy + lh_ / 2 + sy)
                R = (ax1_ + d, acy - lh_ / 2 + sy, ax1_ + d + lw_, acy + lh_ / 2 + sy)
                U = (acx - lw_ / 2 + sx, ay1_ + d, acx + lw_ / 2 + sx, ay1_ + d + lh_)
                D = (acx - lw_ / 2 + sx, ay0_ - d - lh_, acx + lw_ / 2 + sx, ay0_ - d)
                order = [L, R, U, D] if left_first else [R, L, U, D]
                for j, r in enumerate(order):
                    cands.append((d + abs(s) * 0.8 + j * 0.15, r))
            cands.sort(key=lambda c: c[0])
            for score, r in cands:
                if r[0] < x0 + 0.3 or r[2] > x1 - 0.3 or r[1] < y0 + 0.3 or r[3] > y1 - 0.3:
                    continue
                if overlaps(r, occupied) or overlaps(r, placed, 0.35):
                    continue
                best = r
                break
            if best:
                break
        if not best:
            best = (acx, acy, acx + lw_, acy + lh_)
        placed.append(best)
        bx0_, by0_, bx1_, by1_ = best
        col = C["probe"] if it["kind"] == "probe" else C["stage"]
        # one leader per member: label's nearest edge point -> member's nearest point
        for mx0, my0, mx1, my1 in it["members"]:
            mcx, mcy = (mx0 + mx1) / 2, (my0 + my1) / 2
            lx = min(max(mcx, bx0_), bx1_); ly = min(max(mcy, by0_), by1_)
            tx = min(max(lx, mx0), mx1); ty = min(max(ly, my0), my1)
            if math.hypot(lx - tx, ly - ty) > 0.2:
                ax.plot([lx, tx], [ly, ty], color="#ffffff", lw=0.42 * ppm * 0.72, zorder=19,
                        solid_capstyle="round")
                ax.plot([lx, tx], [ly, ty], color=col, lw=0.22 * ppm * 0.72, zorder=19.5,
                        solid_capstyle="round")
        ax.add_patch(FancyBboxPatch((bx0_, by0_), bx1_ - bx0_, by1_ - by0_,
                                    boxstyle="round,pad=0,rounding_size=0.35",
                                    fc=C["label_bg"], ec=col, lw=0.16 * ppm * 0.72, zorder=20))
        first, rest = it["lines"][0], it["lines"][1:]
        ax.text(bx0_ + pad, by1_ - pad, "\n".join(it["lines"]), fontsize=fs, family="DejaVu Sans",
                linespacing=1.15, color=C["label_fg"], ha="left", va="top", zorder=21)

    for px, py, _ in probes:
        ax.add_patch(Circle((px, py), 0.85, fill=False, ec=C["probe"], lw=0.3 * ppm * 0.72, zorder=18))
        ax.add_patch(Circle((px, py), 0.22, color=C["probe"], zorder=18))

    if title:
        ax.text(x0 + 0.8, y1 - 0.8, title, fontsize=2.0 * ppm * 0.72, color="#ffffff",
                weight="bold", ha="left", va="top", zorder=25,
                bbox=dict(boxstyle="round,pad=0.3", fc="#000000", ec="none", alpha=0.55))
    fig.savefig(out, dpi=100, facecolor=fig.get_facecolor())
    plt.close(fig)
