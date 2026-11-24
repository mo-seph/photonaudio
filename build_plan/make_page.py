"""Write build_plan/index.html, the build-and-test page, from stages.py.

Run make_images.py first (the page reads the picture sizes).
"""
import html
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import brd          # noqa: E402
import stages as S  # noqa: E402

E = html.escape
B = brd.Board(os.path.join(HERE, "..", "schematics", "Quad LED Driver Board.brd"))
SM = S.strip_map(B)


def img(name, alt, cls=""):
    w, h = Image.open(os.path.join(HERE, "img", name)).size
    return (f'<a class="shot {cls}" href="img/{name}" target="_blank" rel="noopener">'
            f'<img src="img/{name}" alt="{E(alt)}" width="{w}" height="{h}" loading="lazy"></a>')


def fig(name, alt, caption, cls=""):
    return f'<figure class="{cls}">{img(name, alt)}<figcaption>{caption}</figcaption></figure>'


def parts_table(stage, rows):
    out = ['<div class="tablewrap"><table class="parts"><thead><tr>'
           '<th class="ck"><span class="sr">Fitted</span></th><th>Ref</th><th>Value</th>'
           '<th>Part</th><th>Note</th></tr></thead><tbody>']
    for ref, val, part, note in rows:
        k = f"{stage}-p-{ref}"
        out.append(f'<tr><td class="ck"><input type="checkbox" id="{k}" data-k="{k}" '
                   f'aria-label="{E(ref)} fitted"></td><td class="ref">{E(ref)}</td>'
                   f'<td class="val">{E(val)}</td><td>{E(part)}</td><td>{E(note)}</td></tr>')
    out.append("</tbody></table></div>")
    return "".join(out)


def tests_table(stage, rows):
    out = ['<div class="tablewrap"><table class="tests"><thead><tr>'
           '<th class="ck"><span class="sr">Done</span></th><th class="n">#</th><th>Do</th>'
           '<th>Probe</th><th>Expect</th><th>Reading</th></tr></thead><tbody>']
    for i, (do, probe, expect) in enumerate(rows, 1):
        k = f"{stage}-t-{i}"
        out.append(f'<tr><td class="ck"><input type="checkbox" id="{k}" data-k="{k}" '
                   f'aria-label="step {i} done"></td><td class="n">{i}</td><td>{E(do)}</td>'
                   f'<td class="probe">{E(probe)}</td><td class="expect">{E(expect)}</td>'
                   f'<td class="rd"><input type="text" id="{k}-r" data-k="{k}-r" '
                   f'aria-label="step {i} reading" placeholder="—"></td></tr>')
    out.append("</tbody></table></div>")
    return "".join(out)


def strip_rows(X):
    rows, sm = S.channel_parts(B, X)
    return rows


def empties(X):
    sm = SM[X]
    li = [f'<li><span class="ref">{E(sm[r])}</span> {E(why)}</li>' for r, why in S.LEAVE_EMPTY_A]
    op = [f'<li><span class="ref">{E(sm[r])}</span> {E(why)}</li>' for r, why in S.OPTIONAL_A]
    return li, op


def stage4_table():
    out = ['<div class="tablewrap"><table class="parts quad"><thead><tr><th>Value</th><th>Part</th>'
           '<th>A</th><th>B</th><th>C</th><th>D</th><th>Note</th></tr></thead><tbody>']
    for r, val, part, note in S.CHANNEL_A:
        cells = [f'<td class="ref done">{E(SM["A"][r])}</td>']
        for X in "BCD":
            ref = SM[X][r]
            k = f"s4-p-{ref}"
            cells.append(f'<td class="ref"><label><input type="checkbox" id="{k}" data-k="{k}" '
                         f'aria-label="{E(ref)} fitted"> {E(ref)}</label></td>')
        note = note.replace("U8", "the op-amp").replace(", by C17 (not in the strip)", ", by C17")
        out.append(f'<tr><td class="val">{E(val)}</td><td>{E(part)}</td>{"".join(cells)}'
                   f'<td>{E(note)}</td></tr>')
    out.append("</tbody></table></div>")
    return "".join(out)


def stage4_tests():
    rows = []
    for X in "BCD":
        sm = SM[X]
        sel, r13 = S.BIAS_SEL[X], sm["R51"]
        letter = X.lower()
        rows += [
            (f"Strip {X}: jumper {sel} on POT, trimmer to 0, LED in {sm['J_LED2']}, 12 V on", "LED", "off"),
            (f"Strip {X}: trimmer sweep", f"{sel} middle pin (Vbias)", "0 → ≈ 3.27 V"),
            (f"Strip {X}: trimmer at full", f"across {r13} (4.7 Ω)", "≈ 0.44 V (≈ 94 mA)"),
            (f"Strip {X}: jumper to DAC; {letter} 4095, then {letter} 0", f"{r13}, LED", "full, then fully off"),
            (f"Strip {X}: audio into {sm['AUDIO_IN2']}", "pickup", "as strip A"),
        ]
    return rows + S.S4_TESTS_ALL


li_A, op_A = empties("A")
li_BCD = []
for X in "BCD":
    a, _ = empties(X)
    li_BCD += a
op_BCD = []
for X in "BCD":
    _, o = empties(X)
    op_BCD += o

STAGES = [
    ("s0", "0", "Bare board", "meter only"),
    ("s1", "1", "Power", "limit 100 mA"),
    ("s2", "2", "Channel A", "limit 200 mA"),
    ("s3", "3", "XIAO + DAC", "limit 300 mA"),
    ("s4", "4", "Channels B–D", "limit 600 mA"),
]

nav = "".join(
    f'<a class="stagechip" href="#{sid}"><span class="snum">{num}</span>'
    f'<span class="sname">{E(name)}</span><span class="sprog" data-progress="{sid}">0/0</span></a>'
    for sid, num, name, _ in STAGES)

CSS = r"""
:root{
  /* Layout: one reading column; channel stages put the tall strip picture beside its checklist */
  --bg:#eef2ef; --surface:#ffffff; --ink:#17201c; --muted:#56655e; --line:#d3dcd7;
  --pcb:#22433a; --pcb-ink:#e6efe9; --amber:#a8661a; --amber-fill:#f0a43a; --amber-soft:#fbecd5;
  --cyan:#14798e; --cyan-soft:#d7eff3; --red:#b93a2b; --ok:#2c7a4b; --ok-soft:#dcefe2;
  --f-display:"Space Grotesk",ui-sans-serif,system-ui,sans-serif;
  --f-body:"Inter",ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;
  --f-mono:"JetBrains Mono",ui-monospace,"SF Mono",Menlo,Consolas,monospace;
}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){
  --bg:#0e1412; --surface:#151d1a; --ink:#e3ebe6; --muted:#95a49d; --line:#283430;
  --pcb:#1b382f; --pcb-ink:#e6efe9; --amber:#f0a43a; --amber-fill:#f0a43a; --amber-soft:#3a2a12;
  --cyan:#4cc6dc; --cyan-soft:#12313a; --red:#f0705f; --ok:#62c78c; --ok-soft:#163323; color-scheme:dark}}
:root[data-theme="dark"]{
  --bg:#0e1412; --surface:#151d1a; --ink:#e3ebe6; --muted:#95a49d; --line:#283430;
  --pcb:#1b382f; --pcb-ink:#e6efe9; --amber:#f0a43a; --amber-fill:#f0a43a; --amber-soft:#3a2a12;
  --cyan:#4cc6dc; --cyan-soft:#12313a; --red:#f0705f; --ok:#62c78c; --ok-soft:#163323; color-scheme:dark}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--ink);font:15px/1.55 var(--f-body);
  padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));
  padding-block:0 64px}
.wrap{max-width:1180px;margin:0 auto}
header.top{padding-block:40px 18px;display:grid;gap:10px}
.eyebrow{font:600 12px/1 var(--f-mono);letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
h1{font:700 clamp(28px,4.4vw,44px)/1.08 var(--f-display);margin:0;text-wrap:balance;letter-spacing:-.01em}
.lede{max-width:68ch;color:var(--muted);margin:0}
nav.stages{position:sticky;top:env(safe-area-inset-top,0px);z-index:5;background:var(--bg);
  display:flex;gap:8px;flex-wrap:wrap;padding-block:10px;border-bottom:1px solid var(--line)}
body::before{content:"";position:fixed;inset:0 0 auto;height:env(safe-area-inset-top,0px);z-index:10;background:var(--bg)}
.stagechip{display:flex;align-items:center;gap:8px;padding:7px 12px 7px 8px;border:1px solid var(--line);
  border-radius:999px;background:var(--surface);color:var(--ink);text-decoration:none;font-size:14px}
.stagechip:hover{border-color:var(--amber)}
.stagechip:focus-visible,button:focus-visible,input:focus-visible,a.shot:focus-visible{outline:2px solid var(--cyan);outline-offset:2px}
.snum{display:grid;place-items:center;width:24px;height:24px;border-radius:50%;background:var(--pcb);color:var(--pcb-ink);
  font:700 13px/1 var(--f-mono)}
.sprog{font:500 12px/1 var(--f-mono);color:var(--muted);font-variant-numeric:tabular-nums}
.stagechip.complete .snum{background:var(--ok)}
.stagechip.complete .sprog{color:var(--ok)}
.intro{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,320px),1fr));gap:16px;margin-block:22px 8px}
.card{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:16px 18px;min-width:0}
.card h3{margin:0 0 8px;font:600 15px/1.3 var(--f-display)}
.card ul{margin:0;padding-left:18px;display:grid;gap:4px}
.legend{display:grid;gap:8px}
.lg{display:flex;align-items:center;gap:10px}
.sw{flex:none;width:30px;height:18px;border-radius:4px;border:1px solid var(--line)}
.sw.amber{background:#f0a43a;border-color:#ffcf7a}
.sw.dark{background:#2a2b2f;border-color:#80858c}
.sw.red{background:repeating-linear-gradient(45deg,transparent 0 4px,#e24b3f 4px 6px);border:1.5px dashed #e24b3f}
.sw.cyan{background:#22433a;border-radius:50%;width:18px;box-shadow:inset 0 0 0 3px #35c2dc}
section.stage{padding-block:36px 8px;border-top:1px solid var(--line);margin-top:28px;scroll-margin-top:64px}
.stagehead{display:flex;flex-wrap:wrap;align-items:baseline;gap:6px 14px}
.stagehead h2{font:700 clamp(24px,3.2vw,32px)/1.1 var(--f-display);margin:0;text-wrap:balance}
.stagehead .num{font:600 13px/1 var(--f-mono);color:var(--amber);letter-spacing:.06em;text-transform:uppercase}
.limit{font:600 12px/1 var(--f-mono);padding:5px 9px;border-radius:999px;background:var(--cyan-soft);color:var(--cyan)}
.goal{max-width:72ch;margin:8px 0 0}
h3.step{font:600 18px/1.25 var(--f-display);margin:26px 0 10px;display:flex;gap:10px;align-items:center}
h3.step .tag{font:600 11px/1 var(--f-mono);letter-spacing:.08em;text-transform:uppercase;padding:5px 8px;border-radius:5px}
h3.step .tag.fit{background:var(--amber-soft);color:var(--amber)}
h3.step .tag.test{background:var(--cyan-soft);color:var(--cyan)}
figure{margin:0;display:grid;gap:6px;min-width:0}
figcaption{font-size:13px;color:var(--muted)}
a.shot{display:block;border-radius:8px;overflow:hidden;border:1px solid var(--line);background:#1b3a31;line-height:0}
a.shot img{width:100%;height:auto;display:block}
.twocol{display:grid;grid-template-columns:minmax(0,5fr) minmax(0,7fr);gap:22px;align-items:start}
.twocol > figure{position:sticky;top:70px}
.twocol .tall a.shot img{max-height:calc(100vh - 110px);width:auto;max-width:100%;margin:0 auto}
@media (max-width:820px){.twocol{grid-template-columns:1fr}.twocol > figure{position:static}
  .twocol .tall a.shot img{max-height:none;width:100%}}
.stack{display:grid;gap:14px}
.tablewrap{overflow-x:auto;border:1px solid var(--line);border-radius:10px;background:var(--surface)}
table{border-collapse:collapse;width:100%;font-size:14px}
th{text-align:left;font:600 11.5px/1.2 var(--f-mono);letter-spacing:.06em;text-transform:uppercase;color:var(--muted);
  padding:10px 10px;border-bottom:1px solid var(--line);white-space:nowrap}
td{padding:8px 10px;border-bottom:1px solid var(--line);vertical-align:top}
tbody tr:last-child td{border-bottom:0}
td.ref,.ref{font:600 13.5px/1.4 var(--f-mono);white-space:nowrap}
td.val{white-space:nowrap}
td.n,th.n{font:500 13px/1.4 var(--f-mono);color:var(--muted);width:2.5em;font-variant-numeric:tabular-nums}
td.probe{font:13px/1.45 var(--f-mono);color:var(--cyan)}
td.expect{font-weight:600}
td.ck,th.ck{width:36px;text-align:center;padding-inline:6px}
input[type=checkbox]{width:18px;height:18px;accent-color:var(--ok);margin:2px 0 0;cursor:pointer}
tr:has(input[type=checkbox]:checked) td{background:var(--ok-soft)}
table.quad td.ref label{display:inline-flex;gap:6px;align-items:center;cursor:pointer}
table.quad tr:has(input:checked) td{background:none}
table.quad td.ref:has(input:checked){background:var(--ok-soft)}
td.done{color:var(--muted);font-weight:500}
td.rd{min-width:110px}
td.rd input{width:100%;min-width:90px;font:13px/1.3 var(--f-mono);padding:5px 7px;border:1px solid var(--line);
  border-radius:6px;background:var(--bg);color:var(--ink)}
.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}
.note{border-left:3px solid var(--amber-fill);background:var(--amber-soft);padding:10px 14px;border-radius:0 8px 8px 0;max-width:80ch}
.note.warn{border-color:var(--red);background:color-mix(in srgb,var(--red) 10%,var(--surface))}
.note p{margin:0}
.empties{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,300px),1fr));gap:14px}
.empties ul{margin:0;padding-left:18px;display:grid;gap:3px}
.empties .ref{color:var(--red)}
.empties .opt .ref{color:var(--muted)}
details.trouble{margin-top:14px;background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:10px 16px}
details.trouble summary{cursor:pointer;font-weight:600}
details.trouble ul{margin:10px 0 4px;padding-left:18px;display:grid;gap:6px}
.tabs{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px}
.tabs button{font:600 13px/1 var(--f-mono);padding:8px 14px;border-radius:7px;border:1px solid var(--line);
  background:var(--surface);color:var(--ink);cursor:pointer}
.tabs button[aria-selected="true"]{background:var(--pcb);color:var(--pcb-ink);border-color:var(--pcb)}
code,kbd{font:13px/1.4 var(--f-mono);background:color-mix(in srgb,var(--ink) 7%,transparent);padding:1px 5px;border-radius:4px}
footer{margin-top:44px;padding-top:16px;border-top:1px solid var(--line);color:var(--muted);font-size:13px}
.reset{font:600 12px/1 var(--f-mono);padding:7px 10px;border-radius:6px;border:1px solid var(--line);background:var(--surface);color:var(--muted);cursor:pointer}
.reset[data-armed="1"]{border-color:var(--red);color:var(--red)}
@media (prefers-reduced-motion:no-preference){.stagechip,.tabs button{transition:border-color .15s,background .15s}}
"""

JS = r"""
(function(){
  var KEY="qld-bringup-v1", state={};
  try{state=JSON.parse(localStorage.getItem(KEY)||"{}")||{}}catch(e){state={}}
  function save(){try{localStorage.setItem(KEY,JSON.stringify(state))}catch(e){}}
  var inputs=document.querySelectorAll("input[data-k]");
  function progress(){
    document.querySelectorAll("section[data-stage]").forEach(function(sec){
      var s=sec.getAttribute("data-stage");
      var boxes=sec.querySelectorAll("input[type=checkbox][data-k]");
      var n=0; boxes.forEach(function(b){if(b.checked)n++});
      var chip=document.querySelector('[data-progress="'+s+'"]');
      if(chip){chip.textContent=n+"/"+boxes.length;
        chip.parentNode.classList.toggle("complete",boxes.length>0&&n===boxes.length)}
    });
  }
  inputs.forEach(function(el){
    var k=el.getAttribute("data-k");
    if(el.type==="checkbox"){el.checked=!!state[k];
      el.addEventListener("change",function(){state[k]=el.checked;save();progress()});}
    else{el.value=state[k]||"";
      el.addEventListener("input",function(){state[k]=el.value;save()});}
  });
  progress();
  document.querySelectorAll(".tabs").forEach(function(t){
    var btns=t.querySelectorAll("button");
    btns.forEach(function(b){b.addEventListener("click",function(){
      btns.forEach(function(o){o.setAttribute("aria-selected",o===b?"true":"false");
        var p=document.getElementById(o.getAttribute("aria-controls")); if(p)p.hidden=(o!==b);});
    })});
  });
  var r=document.getElementById("reset");
  if(r){r.addEventListener("click",function(){
    if(r.getAttribute("data-armed")!=="1"){r.setAttribute("data-armed","1");r.textContent="Click again to clear every tick and reading";return;}
    state={};save();inputs.forEach(function(el){if(el.type==="checkbox")el.checked=false;else el.value="";});
    progress();r.setAttribute("data-armed","0");r.textContent="Cleared";});}
})();
"""


def page():
    p = []
    p.append('<title>Quad LED Driver Bring-up</title>\n'
             '<meta name="claude:viewport-fit-sides" content="cover">\n'
             '<link rel="preconnect" href="https://fonts.googleapis.com">'
             '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
             '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700'
             '&family=JetBrains+Mono:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap">\n'
             f"<style>{CSS}</style>\n")
    p.append('<div class="wrap">')
    p.append('<header class="top"><div class="eyebrow">LEDAudioDriver · Quad LED Driver v1.0 · build and test</div>'
             '<h1>Build it a section at a time, and test each section before the next one needs it</h1>'
             '<p class="lede">Five stages: bare board, power, one channel, the XIAO and DAC, then the other three channels. '
             'Each stage has a picture of where the parts go, a checklist, a picture of where to probe, and the readings to expect. '
             'Designators are the ones printed on the board. Your ticks and readings are saved in this browser only.</p></header>')
    p.append(f'<nav class="stages" aria-label="Stages">{nav}</nav>')

    p.append('<div class="intro">'
             '<div class="card legend"><h3>Reading the pictures</h3>'
             '<div class="lg"><span class="sw amber"></span><span>Fit in this stage</span></div>'
             '<div class="lg"><span class="sw dark"></span><span>Fitted in an earlier stage</span></div>'
             '<div class="lg"><span class="sw red"></span><span>Leave empty</span></div>'
             '<div class="lg"><span class="sw cyan"></span><span>Probe here</span></div>'
             '<p style="margin:6px 0 0;color:var(--muted);font-size:13.5px">Component side, the right way up for the silkscreen: XIAO top left, DC jack bottom left. '
             'Polarity marks: <b>band</b> = diode cathode, <b>+</b> = positive pad, <b>dot</b> = pin 1. Click a picture for full size.</p></div>'
             '<div class="card"><h3>On the bench</h3><ul>'
             '<li>Bench supply at 12 V with a current limit; each stage gives the limit to set</li>'
             '<li>Multimeter. LED current = voltage across the 4.7 Ω sense resistor ÷ 4.7 (0.1 V = 21 mA, 0.44 V = 94 mA)</li>'
             '<li>The 10 mm LED on a 3.5 mm lead, tip = anode</li>'
             '<li>Audio interface, a TRS lead, and the pickup for the listening tests</li>'
             '<li>XIAO ESP32-S3 with its male headers fitted; four jumpers</li></ul></div>'
             '<div class="card"><h3>Ground rules</h3><ul>'
             '<li>Solder each stage in table order: low SMD parts first, through-hole last</li>'
             '<li>12 V off whenever you solder or plug parts in</li>'
             '<li>Never plug an audio lead into an LED jack (marked <b>!! NOT AUDIO !!</b>): it puts 12 V through 47 Ω</li>'
             '<li>Test points are bare holes: probe them directly, or solder a wire loop into a GND point for the black clip</li></ul></div>'
             '</div>')

    # ---------------- stage 0
    p.append('<section class="stage" id="s0" data-stage="s0"><div class="stagehead"><span class="num">Stage 0</span>'
             '<h2>Bare board</h2><span class="limit">meter only</span></div>'
             '<p class="goal">Five minutes with a meter before any solder. The two shorts found in review were fixed in the layout; '
             'this confirms the fab made what was sent, while it is still easy to see.</p>')
    p.append('<h3 class="step"><span class="tag test">Check</span>Resistance, with nothing fitted</h3>')
    p.append(fig("s0_checks.png", "Whole board with the bare-board check points marked",
                 "Probe pairs for the resistance checks. The four sleeve pads are the LED jacks' pin 1 (each strip's collector)."))
    p.append('<div style="height:14px"></div>' + tests_table("s0", S.S0_TESTS))
    p.append('</section>')

    # ---------------- stage 1
    p.append('<section class="stage" id="s1" data-stage="s1"><div class="stagehead"><span class="num">Stage 1</span>'
             '<h2>Power</h2><span class="limit">bench limit 100 mA</span></div>'
             '<p class="goal">The 12 V input, polarity diode and filter, the 3.3 V analog regulator (VR1) and bias filter, '
             'and the 5 V regulator (VR2) that will feed the XIAO. Nothing downstream yet, so the supply current is just the two regulators.</p>')
    p.append(fig("s1_overview.png", "Whole board, power parts highlighted", "Where: the bottom-left quarter. The dashed box is the close-up below."))
    p.append(f'<h3 class="step"><span class="tag fit">Fit</span>{len(S.POWER)} parts</h3>')
    p.append(fig("s1_build.png", "Power section close-up with every part labelled", "VR1 is the 3.3 V regulator and VR2 the 5 V one: check the marking before soldering, they look the same."))
    p.append('<div style="height:14px"></div>' + parts_table("s1", S.POWER))
    p.append('<h3 class="step"><span class="tag test">Test</span>Rails, no load</h3>')
    p.append(fig("s1_probe.png", "Power section with probe points and expected voltages", "Black probe on T_G1 or T_G throughout."))
    p.append('<div style="height:14px"></div>' + tests_table("s1", S.S1_TESTS))
    p.append('<details class="trouble"><summary>If a reading is off</summary><ul>'
             '<li><b>C1 + at 0 V:</b> D3 is backwards (band must be at the upper end).</li>'
             '<li><b>Supply sits at the current limit:</b> a short. Reversed tantalums (C3, C16) are a dead short; so are solder bridges on VR1 / VR2.</li>'
             '<li><b>T_3V3 ≈ 5 V and C3 + ≈ 3.3 V:</b> VR1 and VR2 are swapped. Fix before stage 2: 5 V on the analog rail would also reach the DAC and the XIAO\'s I2C later.</li>'
             '<li><b>T_3V3 near 11 V:</b> VR1 is in the wrong way or not a regulator; its tab must be the output.</li>'
             '<li><b>Regulator warm with nothing attached:</b> oscillation. Check that C16 / C3 are the tantalums (they need some ESR to stay stable).</li></ul></details>')
    p.append('</section>')

    # ---------------- stage 2
    rowsA = strip_rows("A")
    p.append('<section class="stage" id="s2" data-stage="s2"><div class="stagehead"><span class="num">Stage 2</span>'
             '<h2>Channel A</h2><span class="limit">bench limit 200 mA</span></div>'
             '<p class="goal">One complete channel on strip A, driven from its own trimmer (jumper on POT), so it works before any firmware exists. '
             'R_KEL2 is the odd one out: it sits beside C17, not in the strip.</p>')
    p.append(fig("s2_overview.png", "Whole board, strip A highlighted", "Where: strip A, the first of the four vertical strips. Red crosses: leave empty."))
    p.append(f'<h3 class="step"><span class="tag fit">Fit</span>{len(rowsA)} parts</h3>')
    p.append('<div class="twocol"><figure class="tall">'
             + img("s2_build.png", "Strip A close-up with every part labelled")
             + '<figcaption>Strip A, audio jack at the top, LED jack at the bottom.</figcaption></figure>'
             '<div class="stack">' + parts_table("s2", rowsA)
             + fig("s2_star.png", "R_KEL2 beside C17", "R_KEL2, the channel\'s Kelvin link, at the star point next to C17.")
             + '<div class="empties"><div class="card"><h3>Leave empty</h3><ul>' + "".join(li_A) + '</ul></div>'
             '<div class="card opt"><h3>Optional headers</h3><ul>' + "".join(op_A) + '</ul></div></div>'
             '</div></div>')
    p.append('<h3 class="step"><span class="tag test">Test</span>Trimmer first, then the LED, then audio</h3>')
    p.append('<div class="note"><p>Start with the jumper on <b>POT</b> (lower pair of BIAS_SEL2) and nothing in either jack. '
             'Vbias is the header\'s middle pin. The sense voltage is T_EM measured against T_KG, not against ground.</p></div>')
    p.append('<div style="height:14px"></div>')
    p.append('<div class="twocol"><figure>' + img("s2_probe.png", "Strip A test points with expected readings")
             + '<figcaption>Strip A\'s test points. T_LS and T_G1 are beside C17.</figcaption></figure>'
             + '<div class="stack">' + tests_table("s2", S.S2_TESTS) + '</div></div>')
    p.append('<details class="trouble"><summary>If a reading is off</summary><ul>'
             '<li><b>T_O5 ≈ Vbias instead of 0.138 × Vbias:</b> R46 (10k) and R47 (1.6k) are swapped.</li>'
             '<li><b>LED never lights and T_O7 sits at ≈ 3.3 V:</b> U7 isn\'t conducting: check its solder joints and orientation, R50, and that the LED lead has the anode on the tip.</li>'
             '<li><b>LED stuck on with the trimmer at 0:</b> U7 collector–emitter short, or R53 missing (it is what holds zero fully off).</li>'
             '<li><b>T_01 doesn\'t follow Vbias:</b> the jumper isn\'t on POT, or a joint on R42–R45 / U8 pins 1–3.</li>'
             '<li><b>Whine, or a sense reading that wanders:</b> check C30 (1 nF) is fitted; on a scope, T_EM should be flat.</li>'
             '<li><b>Hum with audio connected:</b> compare TRS and TS leads first; R_LIFT2 is the ground-lift option.</li></ul></details>')
    p.append('</section>')

    # ---------------- stage 3
    p.append('<section class="stage" id="s3" data-stage="s3"><div class="stagehead"><span class="num">Stage 3</span>'
             '<h2>XIAO + DAC</h2><span class="limit">bench limit 300 mA</span></div>'
             '<p class="goal">The MCP4728 with its four output filters, the I2C parts, the Qwiic socket, and the XIAO on headers. '
             'Then the DAC takes over channel A’s bias, first from <code>dac_test</code>, then from the real Peripheral firmware.</p>')
    p.append(fig("s3_overview.png", "Whole board, XIAO and DAC parts highlighted", "Where: the top-left quarter."))
    p.append(f'<h3 class="step"><span class="tag fit">Fit</span>{len(S.DAC)} parts</h3>')
    p.append(fig("s3_build.png", "XIAO and DAC close-up with every part labelled",
                 "Solder U5 first while there is room round it: tack one corner, check alignment, then the rest. The letters A–D on the silkscreen mark the four filters."))
    p.append('<div style="height:14px"></div>' + parts_table("s3", S.DAC))
    p.append('<h3 class="step"><span class="tag test">Test</span>Without the XIAO, with it, then firmware</h3>')
    p.append(fig("s3_probe.png", "XIAO and DAC area with probe points", "The DAC B–D checks use the upper pad of C11, C12 and C13."))
    p.append('<div style="height:14px"></div>' + tests_table("s3", S.S3_TESTS))
    p.append('<div class="note" style="margin-top:14px"><p><b>dac_test:</b> <code>pio run -e xiao-s3-board -t upload</code>, then '
             '<code>pio device monitor -e xiao-s3-board</code> in <code>LEDAudioDriver/dac_test</code>. '
             'It starts ramping channel A at boot. Commands: <code>a</code>–<code>d</code> 0–4095, <code>all</code>, <code>ramp 4000</code>, <code>stop</code>, <code>check 10000</code>, <code>stats</code>.</p></div>')
    p.append('<details class="trouble"><summary>If a reading is off</summary><ul>'
             '<li><b>No “device at 0x60”:</b> look for bridges on U5 (pins 2–3 are SCL / SDA); T_SD and T_SC should idle at 3.3 V; check R27 / R28.</li>'
             '<li><b>XIAO doesn\'t boot from 12 V:</b> T_5V good but U4 pin 14 low means D2 is backwards (band at the upper end).</li>'
             '<li><b>DAC writes work but the outputs don\'t move:</b> LDAC (U5 pin 4) must be at ground; on this board it is, so look for an open joint there.</li>'
             '<li><b>After the real firmware, DAC channels power up at full brightness:</b> expected if <code>IDLE_LEVEL</code> 1.0 with <code>EEPROM_SYNC</code> wrote full scale into the DAC\'s EEPROM.</li></ul></details>')
    p.append('</section>')

    # ---------------- stage 4
    p.append('<section class="stage" id="s4" data-stage="s4"><div class="stagehead"><span class="num">Stage 4</span>'
             '<h2>Channels B–D</h2><span class="limit">bench limit 600 mA</span></div>'
             '<p class="goal">The same parts as strip A, three more times. The table lists each part with its designator in every strip; '
             'only the names change. Do one strip at a time and run its tests before starting the next, so a fault stays in one place.</p>')
    p.append(fig("s4_overview.png", "Whole board, strips B to D highlighted", "Where: strips B, C and D. Their three Kelvin links sit beside C17, under R_KEL2."))
    p.append(f'<h3 class="step"><span class="tag fit">Fit</span>{3 * len(S.CHANNEL_A)} parts, {len(S.CHANNEL_A)} per strip</h3>')
    tabs = ('<div class="tabs" role="tablist">'
            + "".join(f'<button role="tab" aria-selected="{"true" if X == "B" else "false"}" aria-controls="tab-{X}" '
                      f'id="tb-{X}">Strip {X}</button>' for X in "BCD") + '</div>')
    panels = "".join(
        f'<div id="tab-{X}" role="tabpanel" aria-labelledby="tb-{X}"{"" if X == "B" else " hidden"}>'
        + img(f"s4_build_{X}.png", f"Strip {X} close-up with every part labelled") + '</div>' for X in "BCD")
    p.append('<div class="twocol"><figure class="tall">' + tabs + panels
             + '<figcaption>Pick a strip. Strip A shows dark: already fitted.</figcaption></figure>'
             '<div class="stack">' + stage4_table()
             + fig("s4_star.png", "Kelvin links for strips B to D beside C17", "The three Kelvin links for B, C and D, under R_KEL2.")
             + '<div class="empties"><div class="card"><h3>Leave empty</h3><ul>' + "".join(li_BCD) + '</ul></div>'
             '<div class="card opt"><h3>Optional headers</h3><ul>' + "".join(op_BCD) + '</ul></div></div>'
             '</div></div>')
    p.append('<h3 class="step"><span class="tag test">Test</span>Each strip, then all four together</h3>')
    p.append(fig("s4_probe.png", "Strips B to D with the bias and sense probe points",
                 "Vbias on each header's middle pin; the sense voltage across each strip's 4.7 Ω resistor (left pad −, right pad +)."))
    p.append('<div style="height:14px"></div>' + tests_table("s4", stage4_tests()))
    p.append('<details class="trouble"><summary>If a reading is off</summary><ul>'
             '<li>Use stage 2’s list with this strip’s names from the table above (R47 → R33 / R61 / R9, and so on).</li>'
             '<li><b>One strip at full whenever its jumper is on DAC:</b> its DAC line is shorted to 3.3 V; measure C11 / C12 / C13’s upper pad against T_3V3.</li>'
             '<li><b>LED supply sags well below 11 V with all four at full:</b> check R24 and R24B are both fitted (1.1 Ω together) and D3 isn\'t hot.</li></ul></details>')
    p.append('</section>')

    p.append('<footer><p>Made from <code>schematics/Quad LED Driver Board.brd</code> (7 Nov 2026, 14:36). '
             'Pictures and this page are generated by <code>LEDAudioDriver/build_plan/make_images.py</code> and <code>make_page.py</code>; '
             'expected readings follow <code>BRINGUP.md</code> and <code>BOM_pcb.md</code> for the 3.3 V, ≈ 95 mA build.</p>'
             '<p><button class="reset" id="reset" type="button">Clear every tick and reading</button></p></footer>')
    p.append('</div>')
    p.append(f"<script>{JS}</script>")
    return "\n".join(p)


if __name__ == "__main__":
    out = os.path.join(HERE, "index.html")
    with open(out, "w") as fh:
        fh.write(page())
    print(out)
