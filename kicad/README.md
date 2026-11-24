# KiCad version of the board

`board/Quad_LED_Driver_Board.kicad_pcb` is `../schematics/Quad LED Driver Board.brd` (the v1.0 board, Fusion export of 2026-11-07 13:36) converted with KiCad 10.0.8's own Eagle importer. There is no KiCad schematic yet: see the end of this file.

## How it was checked (2026-11-24)

| Check | Result |
|---|---|
| Parts | All 182 Fusion parts, plus the 4 mounting holes as `UNK_HOLE_0`…`3` footprints |
| Nets | All 99 nets connect exactly the same pads as in Fusion |
| Copper | 864 top tracks, 140 bottom tracks, 123 vias, 12 pours: the same counts as Fusion |
| Connectivity | 0 unconnected after refilling the pours |
| DRC, with the board's own Fusion rules | 0 errors. 222 warnings, all silkscreen (labels overlapping each other, on pads, or near the edge), which Fusion doesn't check |

**Designators:** KiCad wants every designator to end in a digit, so the importer added a `0` to the 23 that don't: `R24B` → `R24B0`, `T_SC` → `T_SC0`, `PWR_IN` → `PWR_IN0`, `R13B` → `R13B0`, and so on. Those are the only renames.

**Design rules:** the import doesn't carry Fusion's design rules, so `tools/finish_board.py` copies them from the `.brd` (JLCPCB 2-layer: 0.127 mm clearance and track, 0.3 mm drill, 0.9 mm copper to edge, 0.1 mm solder-mask expansion) into the `.kicad_pro`. It also fills the pours.

## Re-running

From this folder, after a new export from Fusion:

```bash
export KICAD_DOCUMENTS_HOME="$PWD/kicad-user"
K=/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli
KPY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/Resources/Python.app/Contents/MacOS/Python
BRD="../schematics/Quad LED Driver Board.brd"
PCB=board/Quad_LED_Driver_Board.kicad_pcb
$K pcb import --format eagle -o $PCB "$BRD"
$KPY tools/finish_board.py "$BRD" $PCB
$KPY tools/check_board_import.py "$BRD" $PCB
$K pcb drc --severity-all -o drc.rpt $PCB
$KPY tools/make_images.py "$BRD" $PCB ../images
```

`KICAD_DOCUMENTS_HOME` stops KiCad from scanning `~/Documents/KiCad` at start-up, which hangs on this Mac. `make_images.py` redraws the two README pictures from a copy of the board with the Fusion designators restored.

## Schematic

KiCad's command line can't import Eagle schematics; only the KiCad window can.

- **The Fusion export:** the cleanest result is a linked schematic and board. For that, export the quad board's own schematic from Fusion as `Quad LED Driver Board.sch`. Then use KiCad's **File → Import Non-KiCad Project → Eagle**, which pairs the `.sch` with the `.brd` of the same name.
- **`check_sch_import.py`:** compares an imported schematic's netlist with the Eagle `.sch`, net by net.
- **Do not use the KiCad MCP server's own Eagle translator.** It was tried on `Driver Channel.sch`: it made every ground symbol a separate part on its own net, so GND and K_GND fell apart.
