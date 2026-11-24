"""Check a KiCad schematic converted from Eagle against the Eagle .sch it came from.

Builds each net as a set of part.pad on both sides (Eagle pin names are mapped to pads
through the device's <connects>; KiCad's come from a kicad-cli netlist), then compares.
Single-pin nets are ignored (KiCad lists every unconnected pin as its own net).

    kicad-cli sch export netlist --format kicadsexpr -o x.net x.kicad_sch
    python3 tools/check_sch_import.py "../schematics/Driver Channel.sch" x.net
"""
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict

sch_path, net_path = sys.argv[1], sys.argv[2]

# --- Eagle: pin name -> pad, per part ---------------------------------------------------
root = ET.parse(sch_path).getroot().find('drawing/schematic')
connects = {}       # (library, deviceset, device) -> {(gate, pin): [pads]}
for lib in root.find('libraries'):
    for ds in lib.find('devicesets'):
        for dev in ds.find('devices'):
            m = {}
            for c in dev.findall('connects/connect'):
                m[(c.get('gate'), c.get('pin'))] = c.get('pad').split()
            connects[(lib.get('name'), ds.get('name'), dev.get('name'))] = m
part_dev = {p.get('name'): (p.get('library'), p.get('deviceset'), p.get('device'))
            for p in root.find('parts')}

e_nets = defaultdict(set)
for sheet in root.find('sheets'):
    for net in sheet.find('nets'):
        for pr in net.iter('pinref'):
            part, gate, pin = pr.get('part'), pr.get('gate'), pr.get('pin')
            for pad in connects.get(part_dev[part], {}).get((gate, pin), []):
                e_nets[net.get('name')].add(f'{part}.{pad}')
e_nets = {n: frozenset(p) for n, p in e_nets.items() if len(p) > 1}

# --- KiCad netlist ----------------------------------------------------------------------
text = open(net_path).read()
text = text[text.index('(nets'):]
starts = list(re.finditer(r'\(net\s+\(code\s+"?\d+"?\)\s+\(name\s+"((?:[^"\\]|\\.)*)"\)', text))
k_nets = {}
for i, m in enumerate(starts):
    block = text[m.end():starts[i + 1].start() if i + 1 < len(starts) else len(text)]
    nodes = re.findall(r'\(node\s+\(ref\s+"([^"]+)"\)\s+\(pin\s+"([^"]+)"\)', block)
    if len(nodes) > 1:
        k_nets[m.group(1).lstrip('/')] = frozenset(f'{r}.{p}' for r, p in nodes)

# KiCad's importer appends "0" to designators without a trailing digit.
k_parts = {p.split('.')[0] for s in k_nets.values() for p in s}
def kref(p):
    part, pad = p.split('.', 1)
    return f'{part if part in k_parts or part + "0" not in k_parts else part + "0"}.{pad}'
e_nets = {n: frozenset(kref(p) for p in s) for n, s in e_nets.items()}

e_sets, k_sets = set(e_nets.values()), set(k_nets.values())
print(f'nets (2+ pins): Eagle {len(e_nets)}, KiCad {len(k_nets)}; identical {len(e_sets & k_sets)}')
for s in sorted(e_sets - k_sets, key=sorted):
    print('  Eagle only:', [n for n, v in e_nets.items() if v == s], sorted(s))
for s in sorted(k_sets - e_sets, key=sorted):
    print('  KiCad only:', [n for n, v in k_nets.items() if v == s], sorted(s))
