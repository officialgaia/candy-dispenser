from manifold3d import Manifold as M, CrossSection as C
import trimesh, numpy as np, base64, io, json
S=72
def cyl(r,h,x=0,y=0,z=0): return M.cylinder(h,r,r,S).translate((x,y,z))
def box(x0,x1,y0,y1,z0,z1): return M.cube((x1-x0,y1-y0,z1-z0)).translate((x0,y0,z0))
def hull(*m): return M.batch_hull(list(m))
def save(m,n): g=m.to_mesh(); trimesh.Trimesh(g.vert_properties[:,:3],g.tri_verts).export(n)
P=6;PR=20;PD=15.5;TD=8;RD=32;WI=33;WO=35.5;PIN=34.25
pins=[np.radians(a+90) for a in(0,120,240)]
# 円盤 Φ64・6穴
d=cyl(RD,TD)+cyl(4,2,z=-2)
for i in range(P): a=2*np.pi*i/P; d-=cyl(PD/2,TD+2,PR*np.cos(a),PR*np.sin(a),-1)
d-=(cyl(2.6,TD+6,z=-3)-box(-5,5,1.55,7,-4,TD+4)-box(-5,5,-7,-1.55,-4,TD+4)); d=d.translate((0,0,2))
save(d,"disc.stl")
# 底板 Φ80
b=cyl(40,3)+(cyl(WO,12)-cyl(WI,13,z=-.5))-cyl(5,5,z=-1)-cyl(8.5,5,0,PR,-1)
for x in(-17.5,17.5): b-=cyl(2.1,5,x,-8,-1)
for a in(30,150,270): b-=cyl(1.7,5,37.7*np.cos(np.radians(a)),37.7*np.sin(np.radians(a)),-1)
for r in pins: b+=cyl(1.1,3,PIN*np.cos(r),PIN*np.sin(r),12)
save(b,"base.stl")
# ホッパー（ふた一体）
H=45; pl=cyl(WO+2,3)
for r in pins: pl-=cyl(1.4,5,PIN*np.cos(r),PIN*np.sin(r),-1)
hop=(pl+hull(cyl(37.5,.5,z=H),cyl(13.5,.5,0,-PR)))-hull(cyl(35.5,.5,z=H+.4),cyl(11,.5,0,-PR,-.4))-cyl(11,10,0,-PR,-2)
save(hop,"hopper.stl")
# 受け皿（ワールド座標、出口は(0,-20)）
tray=box(-20,20,-48,-8,3,30)-hull(box(-18,18,-10.5,-10,8,28),box(-18,18,-50,-49.5,5,28))-cyl(9,5,0,-PR,27)
tray+=box(-20,20,-48,-46,5,9); save(tray,"tray.stl")
# ---- MDF 3mm 平板：お菓子の家 ----
W=44;DI=48;EV=95;PK=125;SH=33
def gable(y):
    cs=C([[(-W,0),(W,0),(W,EV),(0,PK),(-W,EV)]]); return cs.extrude(3).rotate((90,0,0)).translate((0,y,0))
fr=gable(-DI)-box(-20,20,-52,-47,3,28)-cyl(5,6,0,0,0).rotate((90,0,0)).translate((0,-46,106))
bk=gable(DI+3)-box(-6,6,46,53,96,101)
th=np.degrees(np.arctan2(PK-EV,W)); L=np.hypot(W,PK-EV)+6
roof=box(0,L,-DI-6,DI+6,0,3).rotate((0,-th,0)).translate((-W-6*np.cos(np.radians(th)),0,EV-6*np.sin(np.radians(th))))
shelf=box(-41,41,-DI,DI,SH-3,SH)-cyl(10,5,0,-PR,SH-4)-box(-22,22,-7,23,SH-4,SH+1)
mdf=[fr,bk,box(-41,41,-DI,DI,0,3),box(-W,-41,-DI,DI,3,EV),box(41,W,-DI,DI,3,EV),shelf,box(-41,41,30,DI,93,96),roof.mirror((1,0,0))]
Rz=lambda m:m.rotate((0,0,180))
PT={"mdf":M.compose(mdf),"mdf_roof":roof,"base":Rz(b).translate((0,0,SH)),"disc":Rz(d).translate((0,0,SH+1.5)),"hopper":Rz(hop).translate((0,0,SH+12)),"tray":tray,
 "motor":cyl(14,19,0,8,SH-19)+box(-21,21,4,12,SH-1,SH),"rc522":box(-30,30,-48,-46.4,45,85),"ir_rx":box(-6,6,-46,-41,100,112),
 "esp32":box(-11,11,26,48,96,100),"uln2003":box(-17,17,40,48,45,77),"buzzer":box(12,26,42,48,97,105)}
col={"mdf":["#c9a27a",.45],"mdf_roof":["#a0522d",.6],"base":["#8fa3b8",1],"disc":["#e8a33d",1],"hopper":["#6fbf8f",.85],"tray":["#e57373",1],"motor":["#c0c0c8",1],"rc522":["#1976d2",1],"ir_rx":["#333",1],"esp32":["#1565c0",1],"uln2003":["#2e7d32",1],"buzzer":["#222",1]}
out={}
for k,m in PT.items():
    g=m.to_mesh(); bb=io.BytesIO(); trimesh.Trimesh(g.vert_properties[:,:3],g.tri_verts).export(bb,"stl"); out[k]=[base64.b64encode(bb.getvalue()).decode()]+col[k]
js=open("full.js").read(); js=js[js.index(";const r="):]
open("v3.js","w").write('import*as T from"three";import{STLLoader as L}from"three/examples/jsm/loaders/STLLoader.js";import{OrbitControls as O}from"three/examples/jsm/controls/OrbitControls.js";const D='+json.dumps(out)+js.replace("o.target.set(0,0,130)","o.target.set(0,0,60)").replace("c.position.set(330,-380,330)","c.position.set(170,-230,150)").replace("t?.35:1","t?.45:1"))
for n in("disc","base","hopper","tray"): t=trimesh.load(n+".stl"); print(n,t.is_watertight,np.round(t.extents,1))
