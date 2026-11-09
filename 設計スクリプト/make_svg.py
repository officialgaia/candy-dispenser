# MDF 3mm レーザー加工用SVG（単位mm）。赤線=カット、黒塗り=彫刻
import math
from shapely.geometry import Polygon, box, Point
from shapely import affinity
from shapely.ops import unary_union
W,DI,SH,CH,TOP=58.7,66,48,171,200
def hexagon(cx,cy,r=4): return Polygon([(cx+r*math.cos(math.radians(30+60*k)),cy+r*math.sin(math.radians(30+60*k))) for k in range(6)])
def hexes(region,keep,p=9.5,r=4,clear=2.0):
    x0,y0,x1,y1=region.bounds; out=[];i=0;y=y0
    while y<=y1:
        x=x0+(p/2 if i%2 else 0)
        while x<=x1:
            h=hexagon(x,y,r)
            if keep.contains(h.buffer(clear)): out.append(h)
            x+=p
        y+=p*0.866;i+=1
    return out
def crect(u0,v0,u1,v1,c): return Polygon([(u0+c,v0),(u1-c,v0),(u1,v0+c),(u1,v1-c),(u1-c,v1),(u0+c,v1),(u0,v1-c),(u0,v0+c)])
def rbox(cx,cy,w,h,ang): return affinity.rotate(box(cx-w/2,cy-h/2,cx+w/2,cy+h/2),ang,origin=(cx,cy))
def path(poly):
    def ring(cs): cs=list(cs); return "M"+" L".join(f"{x:.2f},{y:.2f}" for x,y in cs[:-1])+" Z"
    return " ".join([ring(poly.exterior.coords)]+[ring(i.coords) for i in poly.interiors])
PARTS=[]
def write(name,outline,holes=(),engrave=(),qty=1,note=""):
    PARTS.append((name,outline,list(holes),list(engrave),qty,note))
    # outline / holes / engrave は (x, 上向きy) で作り、SVGでは上下反転して出力
    allg=unary_union([outline]+list(engrave)); x0,y0,x1,y1=allg.bounds; m=5
    w,h=x1-x0+2*m,y1-y0+2*m
    fl=lambda g: affinity.translate(affinity.scale(g,1,-1,origin=(0,0)),-x0+m,y1+m)
    cut=[outline]+list(holes)
    s=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.2f}mm" height="{h:.2f}mm" viewBox="0 0 {w:.2f} {h:.2f}">',
       f'<title>{name}（{qty}枚）{note}</title>']
    for e in engrave: s.append(f'<path d="{path(fl(e))}" fill="#000000" fill-rule="evenodd" stroke="none"/>')
    for c in cut: s.append(f'<path d="{path(fl(c))}" fill="none" stroke="#FF0000" stroke-width="0.1"/>')
    s.append('</svg>'); open(f"{name}_x{qty}.svg","w").write("\n".join(s))
    print(f"{name}_x{qty}.svg  {w-2*m:.1f} x {h-2*m:.1f} mm  穴{len(holes)}")
sil=Polygon([(-50.7,0),(50.7,0),(W,8),(W,CH),(37,TOP),(-37,TOP),(-W,CH),(-W,8)])
# 正面
drawer=box(-44,3,44,28); irs=box(-10,80,10,83)
slits=[]
for s_ in(-1,1):
    for k in range(2):
        cx=s_*(50+k*3); slits.append(rbox(cx-s_*4.65,36+k*2+9.97,2,22,s_*25))
keep=sil.buffer(-4).intersection(box(-50,153,52,168).buffer(4))
fh=hexes(box(-50,153,52,168),keep)
write("01_front",sil,[drawer,irs]+slits+fh,note="正面")
# 背面
usb=box(-6,3,6,9); keep=sil.buffer(-4).difference(usb.buffer(4))
bh=hexes(box(-48,16,50,167),keep)
write("02_back",sil,[usb]+bh,note="背面")
# 側面（奥行き132 × 高さ163、z=8〜171）
side=box(-DI,8,DI,CH); keep=side.buffer(-4)
sh=hexes(box(-60,14,62,167),keep)
write("03_side",side,sh,qty=2,note="側面")
write("04_bottom",box(-55.7,-DI,55.7,DI),note="底板")
write("05_chamfer_low",box(0,0,math.hypot(8,8),2*DI),qty=2,note="下の斜め板")
write("06_chamfer_top",box(0,0,math.hypot(W-37,TOP-CH),2*DI),qty=2,note="上の斜め板")
write("07_top",box(-37,-DI-3,37,DI+3),[box(-28,-40,28,40)],note="天板（補充口）")
write("08_hatch",box(-31,-43,31,43),[box(-14,-5,14,5)],note="補充口のフタ")
shelf=box(-55.7,-DI,55.7,DI)
write("09_shelf",shelf,[Point(0,-40).buffer(14,64),box(-22,-21,22,9)]+[Point(x,-40).buffer(1.7,32) for x in(-22,22)]+
      [Point(47*math.cos(math.radians(a+180)),-14+47*math.sin(math.radians(a+180))).buffer(1.7,32) for a in(30,150,270)],note="中棚（出口・モーター・ネジ穴）")
arm=Polygon([(-53,40),(53,40),(53,139),(40,149),(-40,149),(-53,139)])
ring=crect(-38,90,38,146,9).difference(crect(-38,90,38,146,9).buffer(-1.4,join_style=2))
write("10_armor",arm,[crect(-32,96,32,140,6),irs]+[sl.intersection(arm.buffer(-1.5)) for sl in slits if sl.intersects(arm.buffer(-1.5))],[ring],note="正面アーマー板（中央＝カード枠）")
write("11_tank_fb",box(0,0,111.4,18),qty=2,note="内箱 前後（外壁の内側いっぱい・外壁に接着）")
write("12_tank_lr",box(0,0,126,18),qty=2,note="内箱 左右（前後板の間に入る・外壁に接着）")
fF=math.hypot(58,69); fB=math.hypot(34,69); fS=math.hypot(35.7,69)   # じょうご：下の口34×34（z81）→上105.4×126（z150＝内箱の内側）
write("13_funnel_front",Polygon([(-52.7,fF),(52.7,fF),(17,0),(-17,0)]),note="じょうご 前（上端を内箱に接着）")
write("14_funnel_back",Polygon([(-52.7,fB),(52.7,fB),(17,0),(-17,0)]),note="じょうご 後ろ")
write("15_funnel_side",Polygon([(-63,fS),(63,fS),(29,0),(-5,0)]),qty=2,note="じょうご 左右")
write("16_drawer_bottom",box(0,0,80,56),note="引き出し 底")
write("17_drawer_long",box(0,0,80,19),qty=2,note="引き出し 前後の壁")
write("18_drawer_short",box(0,0,50,19),qty=2,note="引き出し 左右の壁")
chev=Polygon([(-16,12),(0,6),(16,12),(16,15),(0,9),(-16,15)])
write("19_drawer_face",box(-48,0,48,28),[box(-18,16,18,22)],[chev],note="引き出しの前板")
write("20_rail",box(0,0,56,5),qty=2,note="引き出しのレール")
