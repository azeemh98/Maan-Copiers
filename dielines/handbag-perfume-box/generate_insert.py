"""2-bottle insert (riser tray) for the handbag perfume box. Units: mm.
Inverted tray: a platform with two bottle holes, standing on 4 legs.
Bottles pass through the holes and stand on the box floor."""
import math, sys
from shapely.geometry import Polygon, box as rect
from shapely.ops import unary_union
import cairosvg

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
# ---- box interior (must match generate_dieline.py) ----
WB, DB, DT, H = 115.0, 40.0, 22.0, 85.0
ix, iy = 7.5, (DB-DT)/2
BOARD = 0.5                       # board thickness allowance
# ---- bottle (EDIT to your real bottle) ----
BW, BD, BH = 32.0, 20.0, 80.0     # bottle body width, depth, height incl. cap
CLEAR = 1.0                       # clearance around bottle in hole
GAP = 12.0                        # space between the two bottles
LEG = 25.0                        # platform height above box floor
BLEED = 3.0; TAB = 10.0

# platform size = box interior at height LEG, minus clearance
PW = WB - 2*ix*LEG/H - 2*BOARD - 1.5
PD = DB - 2*iy*LEG/H - 2*BOARD - 1.5
hw, hd = BW + CLEAR, BD + CLEAR
assert 2*hw + GAP < PW - 8, "bottles too wide for platform"
assert hd < PD - 6, "bottle too deep for platform"
# sanity: bottle depth must fit the narrowing box up to its height
assert DB - 2*iy*BH/H - 2*BOARD >= BD, "bottle too tall/deep for sloped walls"
assert BH <= H - 2*BOARD - 2, "bottle too tall for box"

parts = {
 'PLATFORM': rect(0, 0, PW, PD),
 'BACK LEG': rect(0, -LEG, PW, 0),
 'FRONT LEG': rect(0, PD, PW, PD+LEG),
 'LEFT LEG': rect(-LEG, 0, 0, PD),
 'RIGHT LEG': rect(PW, 0, PW+LEG, PD),
}
def tab(x, y0, y1, sgn, t=3.0):
    return Polygon([(x, y0), (x, y1), (x+sgn*TAB, y1 - (t if y1 > y0 else -t)), (x+sgn*TAB, y0 + (t if y1 > y0 else -t))])
tabs = [tab(0, -LEG+0.5, -0.5, -1), tab(PW, -LEG+0.5, -0.5, 1),
        tab(0, PD+0.5, PD+LEG-0.5, -1), tab(PW, PD+0.5, PD+LEG-0.5, 1)]
# tabs should not touch platform corner — shift them off the fold corner
tabs = [t.difference(rect(-LEG-1, -0.01, PW+LEG+1, PD+0.01)) for t in tabs]
cx, cy = PW/2, PD/2
def rhole(x, y, w, h, r=2.0):
    return rect(x-w/2+r, y-h/2+r, x+w/2-r, y+h/2-r).buffer(r, 16)
holes = [rhole(cx-(hw+GAP)/2, cy, hw, hd), rhole(cx+(hw+GAP)/2, cy, hw, hd)]
shape = unary_union(list(parts.values()) + tabs)
cut_shape = shape.difference(unary_union(holes))
bleed = shape.buffer(BLEED, join_style=2, mitre_limit=3)
folds = [((0,0),(PW,0)), ((0,PD),(PW,PD)), ((0,0),(0,PD)), ((PW,0),(PW,PD)),
         ((0,-LEG),(0,0)), ((PW,-LEG),(PW,0)), ((0,PD),(0,PD+LEG)), ((PW,PD),(PW,PD+LEG))]

PGW, PGH = 210.0, 297.0
minx, miny, maxx, maxy = bleed.bounds
ox = (PGW-(maxx-minx))/2 - minx; oy = 95 - miny
def p(x, y): return f"{x+ox:.3f},{y+oy:.3f}"
def path(poly):
    s = ""
    for g in getattr(poly, 'geoms', [poly]):
        s += "M"+" L".join(p(*c) for c in list(g.exterior.coords)[:-1])+" Z "
        for r in g.interiors: s += "M"+" L".join(p(*c) for c in list(r.coords)[:-1])+" Z "
    return s

def build(guides):
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{PGW}mm" height="{PGH}mm" viewBox="0 0 {PGW} {PGH}">',
         '<defs><pattern id="glue" width="3" height="3" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="3" height="3" fill="#fff3c4"/><line x1="0" y1="0" x2="0" y2="3" stroke="#e0b800" stroke-width="0.6"/></pattern></defs>',
         '<rect width="100%" height="100%" fill="white"/>',
         f'<g id="BLEED"><path d="{path(bleed)}" fill="none" stroke="#00a651" stroke-width="0.25" stroke-dasharray="1.5,1"/></g>']
    if guides:
        o.append('<g id="GUIDES">')
        o.append(f'<path d="{path(unary_union(list(parts.values())).difference(unary_union(holes)))}" fill="#f1e4e6" fill-rule="evenodd"/>')
        for t in tabs: o.append(f'<path d="{path(t)}" fill="url(#glue)"/>')
        o.append('</g>')
    o.append(f'<g id="CUT"><path d="{path(cut_shape)}" fill="none" stroke="#e6007e" stroke-width="0.3"/></g><g id="FOLD">')
    for a, b in folds:
        o.append(f'<line x1="{a[0]+ox:.3f}" y1="{a[1]+oy:.3f}" x2="{b[0]+ox:.3f}" y2="{b[1]+oy:.3f}" stroke="#0072bc" stroke-width="0.3" stroke-dasharray="3,1.5"/>')
    o.append('</g>')
    if guides:
        def T(x, y, s, sz=3.2, c="#6b2a35", w="bold", rot=0):
            o.append(f'<text x="{x+ox:.2f}" y="{y+oy:.2f}" font-family="Helvetica,Arial,sans-serif" font-size="{sz}" font-weight="{w}" fill="{c}" text-anchor="middle" transform="rotate({rot} {x+ox:.2f} {y+oy:.2f})">{s}</text>')
        o.append('<g id="LABELS">')
        T(cx, -LEG/2, "BACK LEG"); T(cx, -LEG/2+5, f"{PW:.1f} × {LEG:.0f} mm", 2.4, "#555", "normal")
        T(cx, PD+LEG/2, "FRONT LEG"); T(cx, PD+LEG/2+5, f"{PW:.1f} × {LEG:.0f} mm", 2.4, "#555", "normal")
        T(-LEG/2, cy, "LEFT LEG", 2.6, rot=-90); T(PW+LEG/2, cy, "RIGHT LEG", 2.6, rot=90)
        T(cx, PD-1.2, f"PLATFORM {PW:.1f} × {PD:.1f}", 2.0, "#6b2a35")
        for h in holes:
            c = h.centroid; T(c.x, c.y+0.8, f"{hw:.0f}×{hd:.0f}", 2.2, "#555", "normal")
        for t in tabs:
            c = t.centroid; T(c.x, c.y+0.8, "GLUE", 1.8, "#8a6d00", rot=90)
        o.append('</g>')
        y0 = PGH - 40; x0 = 12
        notes = [
          f"Fits inside: Handbag Perfume Box (W 115 × H 85 × D 40, top 100 × 22). Holds 2 bottles of {BW:.0f} × {BD:.0f} mm, up to {BH:.0f} mm tall.",
          f"Platform sits {LEG:.0f} mm above the box floor; bottles go through the holes and stand on the floor.",
          "Assembly: crease all folds → fold 4 legs down (printed side up) → glue tabs inside the left/right legs → drop into box.",
          "Edit bottle size in generate_insert.py (BW, BD, BH) if your bottles differ, then re-run.",
          "Print: maroon/solid colour on the platform + legs, extend into bleed. Keep glue tabs ink-free.",
        ]
        o.append(f'<g font-family="Helvetica,Arial,sans-serif" fill="#222"><text x="{x0}" y="14" font-size="5" font-weight="bold">2-Bottle Insert — Dieline (1:1, mm, A4)</text>')
        for i, n in enumerate(notes):
            o.append(f'<text x="{x0}" y="{22+i*5}" font-size="2.9" fill="#444">{n}</text>')
        o.append(f'<line x1="{x0}" y1="{y0}" x2="{x0+12}" y2="{y0}" stroke="#e6007e" stroke-width="0.4"/><text x="{x0+15}" y="{y0+1}" font-size="3">Cut</text>'
                 f'<line x1="{x0+30}" y1="{y0}" x2="{x0+42}" y2="{y0}" stroke="#0072bc" stroke-width="0.4" stroke-dasharray="3,1.5"/><text x="{x0+45}" y="{y0+1}" font-size="3">Fold</text>'
                 f'<line x1="{x0+60}" y1="{y0}" x2="{x0+72}" y2="{y0}" stroke="#00a651" stroke-width="0.4" stroke-dasharray="1.5,1"/><text x="{x0+75}" y="{y0+1}" font-size="3">Bleed 3 mm</text>'
                 f'<rect x="{x0+100}" y="{y0-2.5}" width="8" height="5" fill="url(#glue)"/><text x="{x0+111}" y="{y0+1}" font-size="3">Glue</text>'
                 f'<line x1="{x0}" y1="{y0+12}" x2="{x0+100}" y2="{y0+12}" stroke="#000" stroke-width="0.4"/><line x1="{x0}" y1="{y0+10.5}" x2="{x0}" y2="{y0+13.5}" stroke="#000" stroke-width="0.4"/><line x1="{x0+100}" y1="{y0+10.5}" x2="{x0+100}" y2="{y0+13.5}" stroke="#000" stroke-width="0.4"/>'
                 f'<text x="{x0+50}" y="{y0+17}" text-anchor="middle" font-size="2.6">100 mm — check scale after printing</text></g>')
    o.append('</svg>')
    return "\n".join(o)

for name, g in [("insert_with_guides", True), ("insert_print_only", False)]:
    svg = build(g)
    open(f"{OUT}/{name}.svg", "w").write(svg)
    cairosvg.svg2pdf(bytestring=svg.encode(), write_to=f"{OUT}/{name}.pdf")
cairosvg.svg2png(bytestring=build(True).encode(), write_to=f"{OUT}/insert_preview.png", output_width=1240)
print(f"platform {PW:.1f} x {PD:.1f}, holes {hw}x{hd}")
