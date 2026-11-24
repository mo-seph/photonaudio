"""Check a KiCad board imported from Eagle against the Eagle .brd it came from.

Compares parts, nets (as sets of part.pad, so renamed nets still match), track and via
counts, then refills the zones and reports KiCad's unconnected count. Run with KiCad's
Python, with KICAD_DOCUMENTS_HOME set (see kicad/README.md):

    $KPY tools/check_board_import.py "../schematics/Quad LED Driver Board.brd" board/Quad_LED_Driver_Board.kicad_pcb
"""
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict

import pcbnew

brd_path, pcb_path = sys.argv[1], sys.argv[2]

# --- Eagle side -------------------------------------------------------------------------
root = ET.parse(brd_path).getroot()
board = root.find('drawing/board')
e_parts = {el.get('name') for el in board.find('elements')}
e_nets = {}
e_wires = defaultdict(int)
e_vias = 0
for sig in board.find('signals'):
    pads = frozenset(f"{c.get('element')}.{c.get('pad')}" for c in sig.findall('contactref'))
    if pads:
        e_nets[sig.get('name')] = pads
    for w in sig.findall('wire'):
        e_wires[w.get('layer')] += 1
    e_vias += len(sig.findall('via'))
e_polys = sum(len(sig.findall('polygon')) for sig in board.find('signals'))

# --- KiCad side -------------------------------------------------------------------------
pcb = pcbnew.LoadBoard(pcb_path)
k_parts = {fp.GetReference() for fp in pcb.GetFootprints()}
k_net_pads = defaultdict(set)
for fp in pcb.GetFootprints():
    for pad in fp.Pads():
        if pad.GetNetname():
            k_net_pads[pad.GetNetname()].add(f'{fp.GetReference()}.{pad.GetNumber()}')
k_nets = {n: frozenset(p) for n, p in k_net_pads.items()}
k_tracks = defaultdict(int)
k_vias = 0
for t in pcb.GetTracks():
    if t.GetClass() == 'PCB_VIA':
        k_vias += 1
    else:
        k_tracks[pcb.GetLayerName(t.GetLayer())] += 1

# KiCad wants every designator to end in a digit, so its importer appends "0" to the
# ones that don't (R24B -> R24B0, T_SC -> T_SC0). Map Eagle names to KiCad names first.
ref = {n: n if n in k_parts else n + '0' for n in e_parts}
renamed_parts = sorted(f'{n} -> {k}' for n, k in ref.items() if n != k)
e_nets = {name: frozenset(f"{ref[p.split('.')[0]]}.{p.split('.', 1)[1]}" for p in pads)
          for name, pads in e_nets.items()}

print(f'parts:  Eagle {len(e_parts)}, KiCad {len(k_parts)};'
      f' {len(renamed_parts)} designators given a trailing 0')
for name in sorted(set(ref.values()) - k_parts):
    print('  only in Eagle:', name)
for name in sorted(k_parts - set(ref.values())):
    print('  only in KiCad:', name)

print(f'nets with pads:  Eagle {len(e_nets)}, KiCad {len(k_nets)}')
e_sets, k_sets = set(e_nets.values()), set(k_nets.values())
k_by_set = {v: n for n, v in k_nets.items()}
renamed = [(n, k_by_set[s]) for n, s in e_nets.items() if s in k_by_set and k_by_set[s] != n]
for s in e_sets - k_sets:
    print('  Eagle net not matched:', [n for n, v in e_nets.items() if v == s], sorted(s)[:8])
for s in k_sets - e_sets:
    print('  KiCad net not matched:', [n for n, v in k_nets.items() if v == s], sorted(s)[:8])
print(f'  identical pad sets: {len(e_sets & k_sets)} of {len(e_sets)}; renamed: {len(renamed)}')
for old, new in renamed[:20]:
    print(f'    {old!r} -> {new!r}')

print(f"tracks: Eagle top {e_wires.get('1', 0)}, bottom {e_wires.get('16', 0)};"
      f" KiCad F.Cu {k_tracks.get('F.Cu', 0)}, B.Cu {k_tracks.get('B.Cu', 0)}")
print(f'vias:   Eagle {e_vias}, KiCad {k_vias}')
print(f'pours:  Eagle {e_polys}, KiCad zones {len(list(pcb.Zones()))}')

pcbnew.ZONE_FILLER(pcb).Fill(pcb.Zones())
pcb.BuildConnectivity()
print('unconnected after zone refill:', pcb.GetConnectivity().GetUnconnectedCount(True))
