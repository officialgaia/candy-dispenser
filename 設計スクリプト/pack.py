import math, rectpack
from shapely import affinity
from shapely.geometry import box
import make_svg as ms   # 個別SVGも同時に作り直される
BIG=set()  # 全部品を割り付ける
SHEET=(300,225); GAP=3
items=[]
for name,o,h,e,q,note in ms.PARTS:
    if name in BIG: continue
    for i in range(q): items.append((f"{name}#{i}",o,h,e,note))
def path(poly): return ms.path(poly)
packer=rectpack.newPacker(rotation=True,pack_algo=rectpack.MaxRectsBl,sort_algo=rectpack.SORT_SSIDE)
for idx,(n,o,h,e,note) in enumerate(items):
    x0,y0,x1,y1=o.bounds; packer.add_rect(x1-x0+GAP,y1-y0+GAP,rid=idx)
for _ in range(10): packer.add_bin(SHEET[0]-2*5+GAP,SHEET[1]-2*5+GAP)
packer.pack()
sheets={}
for b,x,y,w,h,rid in packer.rect_list(): sheets.setdefault(b,[]).append((x,y,w,h,rid))
assert sum(len(v) for v in sheets.values())==len(items),"入りきらない部品あり"
for b,rects in sorted(sheets.items()):
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{SHEET[0]}mm" height="{SHEET[1]}mm" viewBox="0 0 {SHEET[0]} {SHEET[1]}">',
         f'<title>MDF板 {b+1}枚目（MDF 3mm、{SHEET[0]}×{SHEET[1]}mm）</title>',
         f'<rect x="0" y="0" width="{SHEET[0]}" height="{SHEET[1]}" fill="none" stroke="#0000FF" stroke-width="0.2" stroke-dasharray="4 3"/>']
    labels=[]
    for x,y,w,h,rid in rects:
        n,o,hs,es,note=items[rid]; geoms=[o]+hs+es
        ow,oh=o.bounds[2]-o.bounds[0],o.bounds[3]-o.bounds[1]
        rot = (abs((w-GAP)-ow)>0.01)   # 90°回転して置かれた
        def tf(g):
            g=affinity.scale(g,1,-1,origin=(0,0))                      # 上下反転（SVG座標）
            if rot: g=affinity.rotate(g,90,origin=(0,0))
            gx0,gy0,_,_=affinity.scale(o,1,-1,origin=(0,0)).bounds if not rot else affinity.rotate(affinity.scale(o,1,-1,origin=(0,0)),90,origin=(0,0)).bounds
            return affinity.translate(g,5+x-gx0,5+y-gy0)
        for e in es: out.append(f'<path d="{path(tf(e))}" fill="#000000" fill-rule="evenodd" stroke="none"/>')
        for c in [o]+hs: out.append(f'<path d="{path(tf(c))}" fill="none" stroke="#FF0000" stroke-width="0.1"/>')
        labels.append(f"{n.split('#')[0]}（{note}）")
    out.append("</svg>"); fn=f"sheet{b+1}_300x225.svg"; open(fn,"w").write("\n".join(out))
    print(fn,len(rects),"個:", "、".join(sorted(set(labels))))
