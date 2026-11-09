exec(open("v4.py").read().split("W=44")[0])
def hexes(y0,y1,z0,z1,p=9.5,r=4):
    hs=[];i=0
    for z in np.arange(z0,z1,p*0.866):
        for y in np.arange(y0+(p/2 if i%2 else 0),y1,p): hs.append(M.cylinder(10,r,r,6).rotate((0,90,0)).rotate((90,0,0)).translate((-5,y,z)))
        i+=1
    return M.compose(hs)
def onY(cs,y): return cs.extrude(.6).rotate((90,0,0)).translate((0,y,0))
def onX(cs,x): return cs.extrude(.6).rotate((90,0,0)).rotate((0,0,90)).translate((x,0,0))
def P(pts): return C([pts])
def ring(pts,w=1.4): return P(pts)-P(pts).offset(-w,JT.Miter)
def crect(u0,v0,u1,v1,c): return [(u0+c,v0),(u1-c,v0),(u1,v0+c),(u1,v1-c),(u1-c,v1),(u0+c,v1),(u0,v1-c),(u0,v0+c)]
def stripes(u,v,n=3,w=6,h=40,s=14,gap=11,d=1):  # 斜めのレーシングストライプ
    out=None
    for k in range(n):
        x=u+d*k*gap; pg=P([(x,v),(x+d*w,v),(x+d*(w+s),v+h),(x+d*s,v+h)]) if d>0 else P([(x+d*w,v),(x,v),(x+d*s,v+h),(x+d*(w+s),v+h)])
        out=pg if out is None else out+pg
    return out
def chev(cx,v,w=26,h=10,t=4): return P([(cx-w,v+h),(cx,v),(cx+w,v+h),(cx+w,v+h+t),(cx,v+t),(cx-w,v+h+t)])
W=58.7;DI=66;SH=48;CH=171;TOP=200;WI=55.7
sil=[(-50.7,0),(50.7,0),(W,8),(W,CH),(37,TOP),(-37,TOP),(-W,CH),(-W,8)]
def panel(y,t=3): return P(sil).extrude(t).rotate((90,0,0)).translate((0,y,0))
eng=[]
# 正面
fe=P([(0,0),(1,0),(1,1)]).translate((500,500))
fe=fe
e=onY(fe,-DI-2.4); eng.append(e)
fr=panel(-DI)-hexes(-50,52,153,168).rotate((0,0,90)).translate((0,-DI-1,0))-box(-44,44,-70,-65,3,28)-box(-10,10,-70,-65,70,73)-e
for s in(-1,1):
    for k in range(2): fr-=box(-1,1,-70,-65,0,22).rotate((0,s*-25,0)).translate((s*(50+k*3),0,36+k*2))
# アーマー（カード枠はRC522に合わせて実寸）
oct_=crect(-32,96,32,140,6)
arm_pts=[(-53,40),(53,40),(53,139),(40,149),(-40,149),(-53,139)]
ae=ring(crect(-38,90,38,146,9),1.4)
for sx in(-1,1):
    for sz,z0 in(): ae=ae+P([(sx*72,z0),(sx*72,z0+sz*18),(sx*72-sx*3,z0+sz*18),(sx*72-sx*3,z0+sz*3),(sx*54,z0+sz*3),(sx*54,z0)])  # 角のブラケット
ae=ae
armor=P(arm_pts).extrude(3).rotate((90,0,0)).translate((0,-DI-3,0))-P(oct_).extrude(5).rotate((90,0,0)).translate((0,-DI-2,0))
a_e=onY(ae,-DI-5.4); armor-=a_e; armor-=box(-10,10,-75,-65,70,73); eng.append(a_e)
for s_ in(-1,1):
    for k in range(2): armor-=box(-1,1,-76,-64,0,22).rotate((0,s_*-25,0)).translate((s_*(50+k*3),0,36+k*2))
# 側面：ハニカム帯＋枠線＋ストライプ
hx=hexes(-60,62,14,167)
se=P([(0,0),(1,0),(1,1)]).translate((500,500))
eL=onX(se,-W); eR=onX(se,W-.6); eng+=[eL,eR]
sL=box(-W,-WI,-DI,DI,8,CH)-hx.translate((-W+1,0,0))-eL; sR=box(WI,W,-DI,DI,8,CH)-hx.translate((W-1,0,0))-eR
# 背面
be=P([(0,0),(1,0),(1,1)]).translate((500,500))
eb=onY(be,DI+3); eng.append(eb)
bk=panel(DI+3)-box(-6,6,64,71,3,9)-hexes(-48,50,16,167).rotate((0,0,90)).translate((0,DI+2,0))-eb
mdf=[fr,bk,box(-WI,WI,-DI,DI,0,3),sL,sR,strip((-W,8),(-50.7,0),-DI,DI).translate((2.121,0,2.121)),strip((50.7,0),(W,8),-DI,DI).translate((-2.121,0,2.121)),strip((-W,CH),(-37,TOP),-DI,DI),strip((37,TOP),(W,CH),-DI,DI),
     box(-WI,WI,-DI,DI,SH-3,SH)-cyl(10,5,0,-20,SH-4)-box(-22,22,-7,23,SH-4,SH+1)]
# 3Dプリント：大型じょうご（底はΦ75で底板に乗り、上のつばを棚で受ける）
pins=[np.radians(a+90) for a in(0,120,240)]
pl=cyl(37.5,3)
for r in pins: pl-=cyl(1.4,5,34.25*np.cos(r),34.25*np.sin(r),-1)
fun=(pl+M.batch_hull([cyl(80,.5,z=85),cyl(13.5,.5,0,-20)]))-M.batch_hull([cyl(78,.5,z=85.4),cyl(11,.5,0,-20,-.4)])-cyl(11,10,0,-20,-2)
fun+=cyl(84,3,z=82)-cyl(78,4,z=81.5)
g=fun.to_mesh(); trimesh.Trimesh(g.vert_properties[:,:3],g.tri_verts).export("funnel.stl")
tray=box(-20,20,-99,-8,3,30)-M.batch_hull([box(-18,18,-10.5,-10,22,28),box(-18,18,-101,-100.5,5,28)])-cyl(9,5,0,-20,27)+box(-20,20,-99,-97,5,9)
g=tray.to_mesh(); trimesh.Trimesh(g.vert_properties[:,:3],g.tri_verts).export("tray.stl")
# 引き出し：3Dプリントの箱＋MDFの前板
drawer=box(-40,40,-66,-10,4,26)-box(-37,37,-63,-13,7,30)

dfe=onY(chev(0,6,16,6,3),-72.0)
dface=box(-48,48,-72,-69,2,30)-box(-18,18,-73,-68,18,24)-dfe; eng.append(dfe)
rails=box(-43,-41,-66,-10,3,8)+box(41,43,-66,-10,3,8)
ad=pl+(M.batch_hull([box(-22,22,-42,2,14,15),cyl(13.5,.5,0,-20)])-M.batch_hull([box(-20,20,-40,0,14.5,15.5),cyl(11,.5,0,-20,-.4)]))-cyl(11,10,0,-20,-2)
g=ad.to_mesh(); trimesh.Trimesh(g.vert_properties[:,:3],g.tri_verts).export("adapter.stl")
def plate4(a,b,c,d,t=3):
    q=lambda p:box(p[0]-t/2,p[0]+t/2,p[1]-t/2,p[1]+t/2,p[2]-t/2,p[2]+t/2)
    return M.batch_hull([q(a),q(b),q(c),q(d)])
zb,zt=SH+12+15,140
fpan=M.compose([plate4((-52,-61,zt),(52,-61,zt),(20,0,zb),(-20,0,zb)),plate4((-52,61,zt),(52,61,zt),(20,40,zb),(-20,40,zb)),
                plate4((-52,-61,zt),(-52,61,zt),(-20,40,zb),(-20,0,zb)),plate4((52,-61,zt),(52,61,zt),(20,40,zb),(20,0,zb))])
tz0,tz1=29,SH-3
tube=cyl(13,tz1-tz0,0,-20,tz0)-cyl(10,tz1-tz0+2,0,-20,tz0-1)
tube+=box(-24,24,-34,-9,tz1-2.5,tz1)-cyl(10,5,0,-20,tz1-4)              # 中棚にネジ止めするつば
for x in(-19,19): tube-=cyl(1.7,5,x,-20,tz1-4)
tube-=box(9,15,-25,-15,33,41)                                            # センサーの窓（+x側）
tube+=box(13,48,-27,-13,30,32)                                           # センサーを載せる台
g=tube.translate((0,20,-tz0)).to_mesh(); trimesh.Trimesh(g.vert_properties[:,:3],g.tri_verts).export("sensor_tube.stl")
sens=box(15,47,-26,-14,32,34)+box(13,17,-24,-16,34,38)
Rz=lambda m:m.rotate((0,0,180))
PT={"mdf":M.compose(mdf),"engrave":None,"armor":armor,"lid":box(-37,37,-DI-3,DI+3,TOP,TOP+3)-box(-28,28,-40,40,TOP-1,TOP+4),"hatch":box(-31,31,-43,43,TOP+3,TOP+6)-box(-14,14,-5,5,TOP+2,TOP+7),
 "led":box(-55,55,-64.5,-63,30,60),
 "base":Rz(ld("base")).translate((0,0,SH)),"disc":Rz(ld("disc")).translate((0,0,SH+1.5)),"adapter":Rz(ad).translate((0,0,SH+12)),"mdf_funnel":fpan,"mdf_tank":box(-52,52,-61,61,140,168)-box(-49,49,-58,58,139,169),"mdf_drawer":drawer,"drawer_face":dface,"rails":rails,
 "motor":cyl(14,19,0,8,SH-19)+box(-21,21,4,12,SH-1,SH),"rc522":box(-30,30,-64,-62.4,98,138),"ir_rx":box(-6,6,-64,-59,66,76),
 "esp32":box(18,40,44,66,3,7),"uln2003":box(-17,17,58,66,52,84),"buzzer":box(-40,-26,50,66,3,9),"sensor_tube":tube,"sensor":sens}
col={"sensor_tube":["#6fbf8f",1],"sensor":["#2e7d32",1],"mdf":["#1b1b22",.5],"engrave":["#c9a27a",1],"armor":["#2a2a36",1],"lid":["#1b1b22",1],"hatch":["#ff2bd6",1],"led":["#00e5ff",1],"base":["#8fa3b8",1],"disc":["#e8a33d",1],"adapter":["#6fbf8f",1],"mdf_funnel":["#2a2a36",1],"mdf_tank":["#2a2a36",1],"mdf_drawer":["#2a2a36",1],"drawer_face":["#2a2a36",1],"rails":["#1b1b22",1],"motor":["#c0c0c8",1],"rc522":["#1976d2",1],"ir_rx":["#555",1],"esp32":["#1565c0",1],"uln2003":["#2e7d32",1],"buzzer":["#444",1]}
PT['engrave']=M.compose([e for e in eng if max(e.bounding_box()[3:])<400])
import trimesh as _t
sc=_t.Scene()
for k,m in PT.items():
    g=m.to_mesh(); tm=_t.Trimesh(g.vert_properties[:,:3],g.tri_verts)
    c=col[k][0].lstrip('#'); c=''.join(ch*2 for ch in c) if len(c)==3 else c; tm.visual.face_colors=[int(c[0:2],16),int(c[2:4],16),int(c[4:6],16),255]
    sc.add_geometry(tm,node_name=k)
sc.export("assembly.glb"); sc.export("assembly.3mf")
out={}
for k,m in PT.items():
    g=m.to_mesh(); bb=io.BytesIO(); trimesh.Trimesh(g.vert_properties[:,:3],g.tri_verts).export(bb,"stl"); out[k]=[base64.b64encode(bb.getvalue()).decode()]+col[k]
js=open("full.js").read(); js=js[js.index(";const r="):]
js=js.replace("o.target.set(0,0,130)","o.target.set(0,0,95)").replace("c.position.set(330,-380,330)","c.position.set(290,-380,260)").replace("t?.35:1","t?.5:1").replace("0x1e1e22","0xffffff")
open("v14.js","w").write('import*as T from"three";import{STLLoader as L}from"three/examples/jsm/loaders/STLLoader.js";import{OrbitControls as O}from"three/examples/jsm/controls/OrbitControls.js";const D='+json.dumps(out)+js)
for n in("adapter","sensor_tube"): t=trimesh.load(n+".stl"); print(n,t.is_watertight,np.round(t.extents,1))
