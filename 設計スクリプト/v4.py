from manifold3d import Manifold as M, CrossSection as C, JoinType as JT
import manifold3d as m3, trimesh, numpy as np, base64, io, json
S=48
def cyl(r,h,x=0,y=0,z=0,s=S): return M.cylinder(h,r,r,s).translate((x,y,z))
def box(x0,x1,y0,y1,z0,z1): return M.cube((x1-x0,y1-y0,z1-z0)).translate((x0,y0,z0))
def ld(n): t=trimesh.load(n+".stl"); t.merge_vertices(); return M(m3.Mesh(vert_properties=np.array(t.vertices,np.float32),tri_verts=np.array(t.faces,np.uint32)))
def strip(p0,p1,y0,y1):  # (x,z)の2点を結ぶ3mm板
    L=np.hypot(p1[0]-p0[0],p1[1]-p0[1]); a=np.degrees(np.arctan2(p1[1]-p0[1],p1[0]-p0[0]))
    return box(0,L,y0,y1,-3,0).rotate((0,-a,0)).translate((p0[0],0,p0[1]))
W=44;DI=48;SH=33
sil=[(-38,0),(38,0),(44,6),(44,88),(28,110),(-28,110),(-44,88),(-44,6)]
def panel(y,t=3):
    return C([sil]).extrude(t).rotate((90,0,0)).translate((0,y,0))
fr=panel(-DI)-box(-20,20,-52,-47,3,26)                     # 受け取り口
for s in(-1,1):                                            # 光るスリット（斜め）
    for k in range(3): fr-=strip((s*30,20+k*8),(s*40,34+k*8),-52,-47).translate((0,0,1.5)) if False else box(-1,1,-52,-47,0,16).rotate((0,s*-25,0)).translate((s*(33+k*3.2),0,18+k*2))
fr-=box(-6,6,-52,-47,94,97)                                # 赤外線スリット
armor=C([[(-40,30),(40,30),(40,82),(30,96),(-30,96),(-40,82)]]).extrude(3).rotate((90,0,0)).translate((0,-DI-3,0))
armor-=C([[(-28,40),(28,40),(32,46),(32,78),(28,84),(-28,84),(-32,78),(-32,46)]]).extrude(5).rotate((90,0,0)).translate((0,-DI-2,0))  # カードをかざす枠
bk=panel(DI+3)-box(-6,6,46,53,96,101)
side=lambda x0,x1:box(x0,x1,-DI,DI,6,88)
hexv=M.compose([M.cylinder(5,3.6,3.6,6).rotate((0,90,0)).rotate((90,0,0)).translate((0,y+(6 if (i%2) else 0),z)) for i,z in enumerate(range(40,84,7)) for y in range(-36,37,12)])
sL=side(-W,-41)-hexv.translate((-45,0,0)); sR=side(41,W)-hexv.translate((40,0,0))
mdf=[fr,bk,box(-41,41,-DI,DI,0,3),sL,sR,strip((-44,6),(-38,0),-DI,DI),strip((38,0),(44,6),-DI,DI),strip((-44,88),(-28,110),-DI,DI),strip((28,110),(44,88),-DI,DI),
     box(-41,41,-DI,DI,SH-3,SH)-cyl(10,5,0,-20,SH-4)-box(-22,22,-7,23,SH-4,SH+1),box(-38,38,30,DI,93,96)]
Rz=lambda m:m.rotate((0,0,180))
glow=[box(s*(31+k*3.2)-1,s*(31+k*3.2)+1,-47,-46,18+k*2,34+k*2).rotate((0,0,0)) for s in(-1,1) for k in range(3)]
PT={"mdf":M.compose(mdf),"armor":armor,"lid":box(-28,28,-DI-3,DI+3,107,110),"led":M.compose([box(-40,40,-46.5,-45,10,40),box(-30,30,-46.5,-45,88,92)]),
 "base":Rz(ld("base")).translate((0,0,SH)),"disc":Rz(ld("disc")).translate((0,0,SH+1.5)),"hopper":Rz(ld("hopper")).translate((0,0,SH+12)),"tray":ld("tray"),
 "motor":cyl(14,19,0,8,SH-19)+box(-21,21,4,12,SH-1,SH),"rc522":box(-30,30,-45,-43.4,45,85),"ir_rx":box(-6,6,-45,-40,90,100),
 "esp32":box(-11,11,26,48,96,100),"uln2003":box(-17,17,40,48,45,77),"buzzer":box(12,24,42,48,97,103)}
col={"mdf":["#1b1b22",.55],"armor":["#2a2a36",1],"lid":["#ff2bd6",.9],"led":["#00e5ff",1],"base":["#8fa3b8",1],"disc":["#e8a33d",1],"hopper":["#6fbf8f",.8],"tray":["#00e5ff",1],"motor":["#c0c0c8",1],"rc522":["#1976d2",1],"ir_rx":["#555",1],"esp32":["#1565c0",1],"uln2003":["#2e7d32",1],"buzzer":["#444",1]}
out={}
for k,m in PT.items():
    g=m.to_mesh(); bb=io.BytesIO(); trimesh.Trimesh(g.vert_properties[:,:3],g.tri_verts).export(bb,"stl"); out[k]=[base64.b64encode(bb.getvalue()).decode()]+col[k]
js=open("full.js").read(); js=js[js.index(";const r="):]
js=js.replace("o.target.set(0,0,130)","o.target.set(0,0,55)").replace("c.position.set(330,-380,330)","c.position.set(150,-230,140)").replace("t?.35:1","t?.55:1").replace("0x1e1e22","0x0b0b10")
open("v4.js","w").write('import*as T from"three";import{STLLoader as L}from"three/examples/jsm/loaders/STLLoader.js";import{OrbitControls as O}from"three/examples/jsm/controls/OrbitControls.js";const D='+json.dumps(out)+js)
