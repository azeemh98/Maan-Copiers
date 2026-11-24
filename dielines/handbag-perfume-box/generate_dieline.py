import math, sys
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union
import cairosvg

OUT = sys.argv[1]
# ---- finished box size (mm) ----
WB, WT = 115.0, 100.0   # width at bottom / top
DB, DT = 40.0, 22.0     # depth at bottom / top (22 fits 20 mm-deep, 80 mm-tall bottles)
H = 85.0                # vertical height
TAB = 12.0              # glue tab width
BLEED = 3.0
FLAP_SIDE, FLAP_TIP = 42.0, 60.0
EYELET_S = 50.0         # eyelet distance from top edge on flap/front
ix = (WB-WT)/2; iy = (DB-DT)/2
hf = math.hypot(H, iy)  # slant height front/back
hs = math.hypot(H, ix)  # slant height sides
ylid = -hf - DT

def tab(P, Q, inside, w=TAB, taper=7.0):
    dx, dy = Q[0]-P[0], Q[1]-P[1]; L = math.hypot(dx, dy); d = (dx/L, dy/L)
    n = (-d[1], d[0])
    mx, my = (P[0]+Q[0])/2, (P[1]+Q[1])/2
    if (inside[0]-mx)*n[0] + (inside[1]-my)*n[1] > 0: n = (-n[0], -n[1])
    return Polygon([P, Q, (Q[0]+n[0]*w-d[0]*taper, Q[1]+n[1]*w-d[1]*taper),
                    (P[0]+n[0]*w+d[0]*taper, P[1]+n[1]*w+d[1]*taper)])

panels = {}
panels['BOTTOM'] = Polygon([(0,0),(WB,0),(WB,DB),(0,DB)])
panels['FRONT'] = Polygon([(0,DB),(WB,DB),(WB-ix,DB+hf),(ix,DB+hf)])
panels['BACK'] = Polygon([(0,0),(WB,0),(WB-ix,-hf),(ix,-hf)])
L = [(0,0),(-hs,iy),(-hs,DB-iy),(0,DB)]
R = [(WB,0),(WB+hs,iy),(WB+hs,DB-iy),(WB,DB)]
panels['LEFT SIDE'] = Polygon(L); panels['RIGHT SIDE'] = Polygon(R)
panels['LID TOP'] = Polygon([(ix,-hf),(WB-ix,-hf),(WB-ix,ylid),(ix,ylid)])
# flap (envelope) — widens like the front wall it covers
def hw(s): return WT/2 + ix*s/hf
cx = WB/2
fl = [(ix, ylid)]
fl.append((cx-hw(FLAP_SIDE)+0.0, ylid-FLAP_SIDE))
# curved V from left corner to tip to right corner
def qb(p0,p1,p2,n=24): return [((1-t)**2*p0[0]+2*(1-t)*t*p1[0]+t*t*p2[0],(1-t)**2*p0[1]+2*(1-t)*t*p1[1]+t*t*p2[1]) for t in [i/n for i in range(1,n+1)]]
lc = (cx-hw(FLAP_SIDE), ylid-FLAP_SIDE); tip = (cx, ylid-FLAP_TIP); rc = (cx+hw(FLAP_SIDE), ylid-FLAP_SIDE)
fl += qb(lc, (cx-hw(FLAP_SIDE)*0.45, ylid-FLAP_SIDE-2), tip)
fl += qb(tip, (cx+hw(FLAP_SIDE)*0.45, ylid-FLAP_SIDE-2), rc)
fl.append((WB-ix, ylid))
panels['FLAP'] = Polygon(fl)
# dust flaps on lid ends (tuck inside side walls)
def dust(x, sgn):
    return Polygon([(x,-hf),(x,ylid),(x+sgn*16,ylid+3),(x+sgn*18,ylid+7),(x+sgn*18,-hf-1)])
panels['DUST L'] = dust(ix,-1); panels['DUST R'] = dust(WB-ix,1)
tabs = [tab(L[0],L[1],(-40,20)), tab(L[3],L[2],(-40,20)), tab(R[0],R[1],(WB+40,20)), tab(R[3],R[2],(WB+40,20))]
shape = unary_union(list(panels.values())+tabs).buffer(0)
holes = [Point(cx, ylid-EYELET_S).buffer(3.0, 64),          # flap eyelet
         Point(cx, DB+hf-EYELET_S-4).buffer(2.5, 64),       # rope hole on front (knot behind flap)
         Point(ix+14, (-hf+ylid)/2).buffer(2.5, 64),        # handle hole L
         Point(WB-ix-14, (-hf+ylid)/2).buffer(2.5, 64)]     # handle hole R
bleed = shape.buffer(BLEED, join_style=2, mitre_limit=3)
folds = [((0,0),(WB,0)),((0,DB),(WB,DB)),((0,0),(0,DB)),((WB,0),(WB,DB)),
         (L[0],L[1]),(L[3],L[2]),(R[0],R[1]),(R[3],R[2]),
         ((ix,-hf),(WB-ix,-hf)),((ix,ylid),(WB-ix,ylid)),((ix,-hf),(ix,ylid)),((WB-ix,-hf),(WB-ix,ylid))]

minx,miny,maxx,maxy = bleed.bounds
PW, PH = 330.0, 483.0  # 13 x 19 in sheet
ox = (PW-(maxx-minx))/2 - minx; oy = (PH-(maxy-miny))/2 - miny + 10
def p(x,y): return f"{x+ox:.3f},{y+oy:.3f}"
def path(poly):
    s = "M"+" L".join(p(*c) for c in list(poly.exterior.coords)[:-1])+" Z"
    for r in poly.interiors: s += " M"+" L".join(p(*c) for c in list(r.coords)[:-1])+" Z"
    return s

def build(guides):
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{PW}mm" height="{PH}mm" viewBox="0 0 {PW} {PH}">',
         '<rect width="100%" height="100%" fill="white"/>']
    o.append(f'<g id="BLEED"><path d="{path(bleed)}" fill="none" stroke="#00a651" stroke-width="0.25" stroke-dasharray="1.5,1"/></g>')
    if guides:
        o.append('<g id="GUIDES">')
        for name, poly in panels.items():
            if name.startswith('DUST'): continue
            o.append(f'<path d="{path(poly)}" fill="#f4ece1"/>')
        for t in tabs: o.append(f'<path d="{path(t)}" fill="url(#glue)"/>')
        o.append('</g>')
    o.append('<g id="CUT">')
    o.append(f'<path d="{path(shape)}" fill="none" stroke="#e6007e" stroke-width="0.3"/>')
    for h in holes: o.append(f'<path d="{path(h)}" fill="none" stroke="#e6007e" stroke-width="0.3"/>')
    o.append('</g><g id="FOLD">')
    for a,b in folds: o.append(f'<line x1="{a[0]+ox:.3f}" y1="{a[1]+oy:.3f}" x2="{b[0]+ox:.3f}" y2="{b[1]+oy:.3f}" stroke="#0072bc" stroke-width="0.3" stroke-dasharray="3,1.5"/>')
    o.append('</g>')
    if guides:
        o.insert(1, '<defs><pattern id="glue" width="3" height="3" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="3" height="3" fill="#fff3c4"/><line x1="0" y1="0" x2="0" y2="3" stroke="#e0b800" stroke-width="0.6"/></pattern></defs>')
        T = lambda x,y,s,sz=4,c="#6b2a35",w="bold",rot=0: o.append(f'<text x="{x+ox:.2f}" y="{y+oy:.2f}" font-family="Helvetica,Arial,sans-serif" font-size="{sz}" font-weight="{w}" fill="{c}" text-anchor="middle" transform="rotate({rot} {x+ox:.2f} {y+oy:.2f})">{s}</text>')
        o.append('<g id="LABELS">')
        F="#555"
        # FRONT & FLAP artwork is upside-down on the sheet (top of art = top edge of box)
        T(cx, DB+16, "FRONT  (art rotated 180°)", 3.6, rot=180); T(cx, DB+22, f"{WB:.0f} (bottom) → {WT:.0f} (top) × {hf:.1f} mm", 2.4, F, "normal", rot=180)
        T(cx, DB+hf-6, "▲ TOP OF BOX", 2.4, F, rot=180)
        T(cx, DB+hf-EYELET_S-4-5, "rope hole Ø5", 2.2, F, "normal", rot=180)
        T(cx, -hf/2, "BACK"); T(cx, -hf/2+6, f"{WB:.0f} → {WT:.0f} × {hf:.1f} mm", 2.6, F, "normal")
        T(cx, -hf+6, "▲ TOP OF BOX", 2.4, F)
        T(cx, DB/2, "BOTTOM"); T(cx, DB/2+6, f"{WB:.0f} × {DB:.0f} mm", 2.6, F, "normal")
        T(-hs*0.35, DB/2, "LEFT SIDE", 3.6, rot=-90); T(-hs*0.35+5, DB/2, f"{DB:.0f} → {DT:.0f} × {hs:.1f}", 2.2, F, "normal", rot=-90)
        T(-hs+5, DB/2, "▲ TOP", 2.2, F, rot=-90)
        T(WB+hs*0.35, DB/2, "RIGHT SIDE", 3.6, rot=90); T(WB+hs*0.35-5, DB/2, f"{DB:.0f} → {DT:.0f} × {hs:.1f}", 2.2, F, "normal", rot=90)
        T(WB+hs-5, DB/2, "▲ TOP", 2.2, F, rot=90)
        T(cx, (-hf+ylid)/2+1.5, "LID TOP  (handle holes Ø5)", 3.0)
        T(cx, ylid-20, "FLAP (art rotated 180°)", 3.6, rot=180); T(cx, ylid-27, "brand logo + name go here", 2.4, F, "normal", rot=180)
        T(cx, ylid-6, "▲ hinge = top of box", 2.2, F, rot=180)
        T(cx, ylid-EYELET_S+7, "eyelet Ø6", 2.2, F, "normal", rot=180)
        for t,(lx,ly) in zip(tabs, [(-40,-3),(-40,DB+3),(WB+40,-3),(WB+40,DB+3)]):
            c = t.centroid; T(c.x, c.y+1, "GLUE", 2.4, "#8a6d00")
        T(ix-9, (-hf+ylid)/2+1, "TUCK", 2, "#555", rot=-90); T(WB-ix+9, (-hf+ylid)/2+1, "TUCK", 2, "#555", rot=90)
        o.append('</g>')
        # legend / title block
        y0 = PH-18; x0 = 12
        o.append(f'<g id="LEGEND" font-family="Helvetica,Arial,sans-serif" font-size="3.2" fill="#222">'
                 f'<text x="{x0}" y="10" font-size="5" font-weight="bold">Handbag Perfume Box — Dieline (1:1, mm)</text>'
                 f'<text x="{x0}" y="15">Finished: W {WB:.0f} × H {H:.0f} × D {DB:.0f} mm (top {WT:.0f} × {DT:.0f}) · Sheet 13 × 19 in (330 × 483 mm) · Board 300–350 GSM</text>'
                 f'<line x1="{x0}" y1="{y0}" x2="{x0+14}" y2="{y0}" stroke="#e6007e" stroke-width="0.4"/><text x="{x0+17}" y="{y0+1.1}">Cut</text>'
                 f'<line x1="{x0+35}" y1="{y0}" x2="{x0+49}" y2="{y0}" stroke="#0072bc" stroke-width="0.4" stroke-dasharray="3,1.5"/><text x="{x0+52}" y="{y0+1.1}">Fold / crease</text>'
                 f'<line x1="{x0+85}" y1="{y0}" x2="{x0+99}" y2="{y0}" stroke="#00a651" stroke-width="0.4" stroke-dasharray="1.5,1"/><text x="{x0+102}" y="{y0+1.1}">Bleed (3 mm) — extend artwork to here</text>'
                 f'<rect x="{x0+175}" y="{y0-2.5}" width="8" height="5" fill="url(#glue)"/><text x="{x0+186}" y="{y0+1.1}">Glue — keep artwork-free</text>'
                 f'<text x="{x0}" y="{y0+8}" fill="#666">Printed side faces you. Hide the LABELS / GUIDES layers before sending to print. Check 100 mm scale bar →</text>'
                 f'<line x1="{x0+190}" y1="{y0+7}" x2="{x0+290}" y2="{y0+7}" stroke="#000" stroke-width="0.4"/>'
                 f'<line x1="{x0+190}" y1="{y0+5.5}" x2="{x0+190}" y2="{y0+8.5}" stroke="#000" stroke-width="0.4"/><line x1="{x0+290}" y1="{y0+5.5}" x2="{x0+290}" y2="{y0+8.5}" stroke="#000" stroke-width="0.4"/>'
                 f'<text x="{x0+240}" y="{y0+12}" text-anchor="middle" font-size="2.6">100 mm</text></g>')
    o.append('</svg>')
    return "\n".join(o)

for name, g in [("dieline_with_guides", True), ("dieline_print_only", False)]:
    svg = build(g)
    open(f"{OUT}/{name}.svg","w").write(svg)
    cairosvg.svg2pdf(bytestring=svg.encode(), write_to=f"{OUT}/{name}.pdf")
cairosvg.svg2png(bytestring=build(True).encode(), write_to=f"{OUT}/preview.png", output_width=1650)
print("bounds w,h:", maxx-minx, maxy-miny, "hf", hf, "hs", hs)
