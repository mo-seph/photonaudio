"""Read an Eagle / Fusion .brd (XML) into simple geometry for drawing.

Everything is in board millimetres. Only what the build pictures need:
board outline and holes, every element's pads (with nets), its silkscreen
(tPlace) and a body box, top / bottom traces, vias, and plain silkscreen text.
"""
import math
import xml.etree.ElementTree as ET


def parse_rot(s):
    """'MR90' -> (mirror, angle in degrees)."""
    s = s or ""
    mirror = "M" in s
    ang = 0.0
    if "R" in s:
        ang = float(s.split("R")[-1] or 0)
    return mirror, ang


class Xform:
    def __init__(self, x=0.0, y=0.0, rot=""):
        self.x, self.y = float(x), float(y)
        self.mirror, self.ang = parse_rot(rot)
        a = math.radians(self.ang)
        self.c, self.s = math.cos(a), math.sin(a)

    def __call__(self, px, py):
        if self.mirror:
            px = -px
        return (self.x + px * self.c - py * self.s,
                self.y + px * self.s + py * self.c)


def arc_points(x1, y1, x2, y2, curve, n=24):
    """Points along an Eagle wire with a 'curve' (included angle, degrees, CCW)."""
    if not curve:
        return [(x1, y1), (x2, y2)]
    th = math.radians(curve)
    dx, dy = x2 - x1, y2 - y1
    chord = math.hypot(dx, dy)
    r = chord / (2 * math.sin(th / 2))
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    h = r * math.cos(th / 2)
    # centre is to the left of p1->p2 for a CCW (positive) arc
    nx, ny = -dy / chord, dx / chord
    cx, cy = mx + nx * h, my + ny * h
    a1 = math.atan2(y1 - cy, x1 - cx)
    pts = []
    for i in range(n + 1):
        a = a1 + th * i / n
        pts.append((cx + abs(r) * math.cos(a), cy + abs(r) * math.sin(a)))
    return pts


def rect_corners(cx, cy, dx, dy, rot_deg):
    a = math.radians(rot_deg)
    c, s = math.cos(a), math.sin(a)
    out = []
    for ux, uy in ((-dx / 2, -dy / 2), (dx / 2, -dy / 2), (dx / 2, dy / 2), (-dx / 2, dy / 2)):
        out.append((cx + ux * c - uy * s, cy + ux * s + uy * c))
    return out


class Board:
    def __init__(self, path):
        root = ET.parse(path).getroot()
        b = root.find("drawing/board")
        self.outline = []        # list of point lists (layer 20)
        self.holes = []          # (x, y, drill)
        self.texts = []          # dicts: x, y, size, rot, align, text (layer 21)
        self.traces = {1: [], 16: []}   # (points, width)
        self.vias = []           # (x, y, drill, diameter)
        self.elements = {}       # name -> dict

        for w in b.findall("plain/wire"):
            if w.get("layer") == "20":
                self.outline.append(arc_points(*[float(w.get(k)) for k in ("x1", "y1", "x2", "y2")],
                                               float(w.get("curve", 0))))
        for c in b.findall("plain/circle"):
            if c.get("layer") == "20":
                self.holes.append((float(c.get("x")), float(c.get("y")), 2 * float(c.get("radius"))))
        for h in b.findall("plain/hole"):
            self.holes.append((float(h.get("x")), float(h.get("y")), float(h.get("drill"))))
        for t in b.findall("plain/text"):
            if t.get("layer") == "21":
                self.texts.append(dict(x=float(t.get("x")), y=float(t.get("y")),
                                       size=float(t.get("size")), rot=t.get("rot", ""),
                                       align=t.get("align", "bottom-left"), text=t.text or ""))

        # packages, keyed by (library, package); Fusion adds library_urn
        pk = {}
        for lib in b.findall("libraries/library"):
            for p in lib.findall("packages/package"):
                pk[(lib.get("name"), lib.get("urn", ""), p.get("name"))] = p
                pk.setdefault((lib.get("name"), p.get("name")), p)

        pad_net = {}
        for s in b.findall("signals/signal"):
            for c in s.findall("contactref"):
                pad_net[(c.get("element"), c.get("pad"))] = s.get("name")
            for w in s.findall("wire"):
                lay = int(w.get("layer"))
                if lay in self.traces:
                    pts = arc_points(*[float(w.get(k)) for k in ("x1", "y1", "x2", "y2")],
                                     float(w.get("curve", 0)))
                    self.traces[lay].append((pts, float(w.get("width"))))
            for v in s.findall("via"):
                drill = float(v.get("drill"))
                self.vias.append((float(v.get("x")), float(v.get("y")), drill,
                                  float(v.get("diameter", 0)) or max(drill + 0.15, 0.5)))

        for e in b.findall("elements/element"):
            name = e.get("name")
            p = pk.get((e.get("library"), e.get("library_urn", ""), e.get("package"))) \
                or pk.get((e.get("library"), e.get("package")))
            T = Xform(e.get("x"), e.get("y"), e.get("rot"))
            pads, silk, docu, xs, ys = [], [], [], [], []
            if p is not None:
                for sm in p.findall("smd"):
                    _, prot = parse_rot(sm.get("rot"))
                    corners = rect_corners(float(sm.get("x")), float(sm.get("y")),
                                           float(sm.get("dx")), float(sm.get("dy")), prot)
                    poly = [T(*q) for q in corners]
                    cx, cy = T(float(sm.get("x")), float(sm.get("y")))
                    pads.append(dict(name=sm.get("name"), kind="smd", poly=poly, x=cx, y=cy,
                                     net=pad_net.get((name, sm.get("name")))))
                    xs += [q[0] for q in poly]; ys += [q[1] for q in poly]
                for pd in p.findall("pad"):
                    drill = float(pd.get("drill"))
                    dia = float(pd.get("diameter", 0) or 0) or max(drill + 0.8, drill * 1.8)
                    shape = pd.get("shape", "round")
                    _, prot = parse_rot(pd.get("rot"))
                    lx, ly = float(pd.get("x")), float(pd.get("y"))
                    if shape == "long":
                        local = rect_corners(lx, ly, 2 * dia, dia, prot)
                    elif shape == "square":
                        local = rect_corners(lx, ly, dia, dia, prot)
                    elif shape == "octagon":
                        local = [(lx + dia / 2 * math.cos(math.radians(22.5 + 45 * i)),
                                  ly + dia / 2 * math.sin(math.radians(22.5 + 45 * i))) for i in range(8)]
                    else:
                        local = [(lx + dia / 2 * math.cos(math.radians(15 * i)),
                                  ly + dia / 2 * math.sin(math.radians(15 * i))) for i in range(24)]
                    poly = [T(*q) for q in local]
                    cx, cy = T(lx, ly)
                    pads.append(dict(name=pd.get("name"), kind="pad", poly=poly, x=cx, y=cy,
                                     drill=drill, net=pad_net.get((name, pd.get("name")))))
                    xs += [q[0] for q in poly]; ys += [q[1] for q in poly]
                for w in p.findall("wire"):
                    lay = w.get("layer")
                    if lay in ("21", "51"):
                        pts = arc_points(*[float(w.get(k)) for k in ("x1", "y1", "x2", "y2")],
                                         float(w.get("curve", 0)))
                        pts = [T(*q) for q in pts]
                        (silk if lay == "21" else docu).append((pts, float(w.get("width"))))
                        if lay == "21":
                            xs += [q[0] for q in pts]; ys += [q[1] for q in pts]
                for c in p.findall("circle"):
                    if c.get("layer") in ("21",):
                        cx, cy = T(float(c.get("x")), float(c.get("y")))
                        r = float(c.get("radius"))
                        pts = [(cx + r * math.cos(math.radians(10 * i)), cy + r * math.sin(math.radians(10 * i)))
                               for i in range(37)]
                        silk.append((pts, float(c.get("width")) or 0.15))
                        xs += [cx - r, cx + r]; ys += [cy - r, cy + r]
                for rr in p.findall("rectangle"):
                    if rr.get("layer") in ("21",):
                        x1, y1, x2, y2 = (float(rr.get(k)) for k in ("x1", "y1", "x2", "y2"))
                        pts = [T(*q) for q in ((x1, y1), (x2, y1), (x2, y2), (x1, y2), (x1, y1))]
                        silk.append((pts, -1))   # -1 = filled
                for h in p.findall("hole"):
                    hx, hy = T(float(h.get("x")), float(h.get("y")))
                    self.holes.append((hx, hy, float(h.get("drill"))))
            if not xs:
                xs, ys = [float(e.get("x"))], [float(e.get("y"))]
            self.elements[name] = dict(
                name=name, value=e.get("value", ""), package=e.get("package"),
                x=float(e.get("x")), y=float(e.get("y")), rot=e.get("rot", ""),
                pads=pads, silk=silk, docu=docu,
                bbox=(min(xs), min(ys), max(xs), max(ys)))

        allx = [q[0] for seg in self.outline for q in seg]
        ally = [q[1] for seg in self.outline for q in seg]
        self.extent = (min(allx), min(ally), max(allx), max(ally))

    def pad(self, element, padname):
        for p in self.elements[element]["pads"]:
            if p["name"] == padname:
                return p
        raise KeyError((element, padname))
