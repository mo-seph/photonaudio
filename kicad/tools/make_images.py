"""Make the README pictures of the board: a 3D render of the top and a plot of the
copper (top red, bottom blue) with the silkscreen and outline.

Works on a temporary copy of the KiCad board in which the designators the Eagle import
renamed (R24B -> R24B0, T_SC -> T_SC0) get their Fusion names back, so the pictures
match the real board. The KiCad board itself is not changed. Run with KiCad's Python,
with KICAD_DOCUMENTS_HOME set (see kicad/README.md), from the kicad/ folder:

    $KPY tools/make_images.py "../schematics/Quad LED Driver Board.brd" board/Quad_LED_Driver_Board.kicad_pcb ../images
"""
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

import pcbnew

KICAD_CLI = '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
brd_path, pcb_path, out_dir = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(out_dir, exist_ok=True)

eagle_names = {el.get('name') for el in
               ET.parse(brd_path).getroot().find('drawing/board/elements')}

with tempfile.TemporaryDirectory() as tmp:
    stem = os.path.splitext(os.path.basename(pcb_path))[0]
    for ext in ('.kicad_pcb', '.kicad_pro'):
        shutil.copy(os.path.splitext(pcb_path)[0] + ext, os.path.join(tmp, stem + ext))
    copy = os.path.join(tmp, stem + '.kicad_pcb')

    board = pcbnew.LoadBoard(copy)
    restored = 0
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if ref not in eagle_names and ref.endswith('0') and ref[:-1] in eagle_names:
            fp.SetReference(ref[:-1])
            restored += 1
    pcbnew.SaveBoard(copy, board)
    print(f'restored {restored} Fusion designators in the copy')

    render = os.path.join(out_dir, 'board_render_top.png')
    subprocess.run([KICAD_CLI, 'pcb', 'render', '--side', 'top', '--width', '2400',
                    '--height', '1450', '--zoom', '1.55', '--quality', 'high',
                    '--background', 'transparent', '-o', render, copy], check=True)

    svg = os.path.join(tmp, 'routing.svg')
    subprocess.run([KICAD_CLI, 'pcb', 'export', 'svg', '--mode-single',
                    '--layers', 'B.Cu,F.Cu,F.Silkscreen,Edge.Cuts', '--page-size-mode', '2',
                    '--exclude-drawing-sheet', '-o', svg, copy], check=True)
    routing = os.path.join(out_dir, 'board_routing.png')
    subprocess.run(['rsvg-convert', '-b', 'white', '-w', '2400', svg, '-o', routing], check=True)
    print('wrote', render, 'and', routing)
