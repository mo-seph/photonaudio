"""Give a board imported from Eagle the design rules it was checked against in Fusion,
fill its zones, and save it with a .kicad_pro next to it.

`kicad-cli pcb import` writes only the .kicad_pcb; KiCad keeps design rules in the
.kicad_pro, so without this the board would be checked against KiCad's defaults.
The values are the board's own Eagle rules (jlcpcb-2layers.dru, read from the .brd).
Run with KiCad's Python, with KICAD_DOCUMENTS_HOME set (see kicad/README.md):

    $KPY tools/finish_board.py "../schematics/Quad LED Driver Board.brd" board/Quad_LED_Driver_Board.kicad_pcb
"""
import re
import sys
import xml.etree.ElementTree as ET

import pcbnew

brd_path, pcb_path = sys.argv[1], sys.argv[2]

rules = ET.parse(brd_path).getroot().find('drawing/board/designrules')
param = {p.get('name'): p.get('value') for p in rules.findall('param')}


def mm(name):
    """An Eagle length parameter ('5mil', '0.3mm') in KiCad internal units."""
    value, unit = re.fullmatch(r'([\d.]+)(mil|mm)', param[name]).groups()
    return pcbnew.FromMM(float(value) * (0.0254 if unit == 'mil' else 1.0))


board = pcbnew.LoadBoard(pcb_path)
ds = board.GetDesignSettings()
clearance = min(mm(k) for k in ('mdWireWire', 'mdWirePad', 'mdWireVia', 'mdPadPad',
                                'mdPadVia', 'mdViaVia', 'mdSmdPad', 'mdSmdVia', 'mdSmdSmd'))
ds.m_MinClearance = clearance
ds.m_TrackMinWidth = mm('msWidth')
ds.m_MinThroughDrill = mm('msDrill')
ds.m_HoleToHoleMin = mm('mdDrill')
ds.m_ViasMinAnnularWidth = mm('rlMinViaOuter')
ds.m_CopperEdgeClearance = mm('mdCopperDimension')
if param['mlMinStopFrame'] == param['mlMaxStopFrame']:      # fixed mask expansion
    ds.m_SolderMaskExpansion = mm('mlMinStopFrame')
ds.m_NetSettings.GetDefaultNetclass().SetClearance(clearance)

filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
pcbnew.SaveBoard(pcb_path, board)

print('rules from', rules.get('name'))
for label, v in (('clearance', clearance), ('min track', ds.m_TrackMinWidth),
                 ('min drill', ds.m_MinThroughDrill), ('hole to hole', ds.m_HoleToHoleMin),
                 ('via annular ring', ds.m_ViasMinAnnularWidth),
                 ('copper to edge', ds.m_CopperEdgeClearance),
                 ('solder mask expansion', ds.m_SolderMaskExpansion)):
    print(f'  {label}: {pcbnew.ToMM(v):.4f} mm')
print('saved', pcb_path)
