# JLCPCB CAM job and design rules

These are JLCPCB's official files, unmodified. They came from [JLCPCBofficial/jlcpcb-eagle](https://github.com/JLCPCBofficial/jlcpcb-eagle) (MIT licence) on 2026-11-07. JLCPCB's help article [How to Generate Gerber and Drill Files in Autodesk Eagle](https://jlcpcb.com/help/article/how-to-generate-gerber-and-drill-files-in-autodesk-eagle) links to that repo.

| File | What |
|---|---|
| `jlcpcb-2layers.dru` | DRC rules for 2 layers, 1 oz copper, 1.6 mm board (2020). They are stricter than JLCPCB's [current limits](https://jlcpcb.com/capabilities/pcb-capabilities). |
| `jlcpcb_2_layer_v9.cam` | The CAM job in Eagle 9 / Fusion format. It writes one ZIP containing: GTL/GBL copper; GTS/GBS solder mask; GTP/GBP paste; GTO silkscreen (layers 21 + 25) and GBO (22 + 26); GKO board outline (layers 20 + 46); and one XLN drill file. |

Fusion re-saved `jlcpcb_2_layer_v9.cam` on first use (2026-11-07 14:27). It is now job version 9.7.0, with the bottom layer as 304 and Fusion's empty ODB++ / image / assembly sections. The outputs are the same as JLCPCB's.
- "Generate job file" is on, so the ZIP also gets a `gerber_job.gbrjob` (Gerber X2 metadata including the owner's name and email). JLCPCB doesn't need it: untick it in the Gerber settings, or delete it from the ZIP.

## In Fusion

1. **Load the rules.** Open the DRC dialog, use its Load button and pick `jlcpcb-2layers.dru`.
   - Then set **Copper/Dimension back to ~1 mm**. The file sets 0.2 mm, which lets the pours creep up to the 4 mm mounting holes.
   - Loading the rules also resizes every pad and via whose diameter is left on auto. Header pads grow from 1.52 to 1.83 mm; vias shrink from about 0.76 to 0.50 mm. Re-run DRC afterwards.
2. **Run DRC.** Every "Overlap" error is a real short; don't approve any of them.
3. **Run the CAM job.** Go to Manufacturing → CAM Processor, load `jlcpcb_2_layer_v9.cam`, check the preview, then Process Job. Don't use the one-click "Generate CAM data" button.
4. **Check the results.**
   - The slotted pads (jacks, PWR_IN) must appear in the drill preview and in JLCPCB's Gerber viewer. Add an order remark: "plated slots in the jack pads".
   - Layer 51 (tDocu) is **not** printed. Text meant for the silkscreen has to be on layer 21.
