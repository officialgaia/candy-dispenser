# 回路図（ネットラベル方式）：同じ名前のラベルどうしがつながっている
F='font-family="Hiragino Sans, Noto Sans CJK JP, Noto Sans CJK TC, sans-serif"'
o=[]
def T(x,y,s,size=12,anchor="start",w=400,col="#000"): o.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{w}" text-anchor="{anchor}" dominant-baseline="central" fill="{col}" {F}>{s}</text>')
def L(x1,y1,x2,y2,w=1.4): o.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#000" stroke-width="{w}"/>')
def net(x,y,name,side):   # ネットラベル（小さい旗）
    col="#0F6E56"
    if side=="left":  o.append(f'<path d="M{x} {y} l-6 -7 h-{8*len(name)+8} v14 h{8*len(name)+8} z" fill="#E1F5EE" stroke="{col}"/>'); T(x-10,y,name,11,"end",500,col)
    else:             o.append(f'<path d="M{x} {y} l6 -7 h{8*len(name)+8} v14 h-{8*len(name)+8} z" fill="#E1F5EE" stroke="{col}"/>'); T(x+10,y,name,11,"start",500,col)
def gnd(x,y): L(x,y,x,y+8); L(x-9,y+8,x+9,y+8); L(x-6,y+12,x+6,y+12); L(x-3,y+16,x+3,y+16)
def vcc(x,y,name): L(x,y,x,y-8); L(x-8,y-8,x+8,y-8,2); T(x,y-18,name,11,"middle",500)
def block(x,y,w,title,left=(),right=(),sub=""):
    n=max(len(left),len(right),1); h=n*24+16
    o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#FAFAF7" stroke="#000" stroke-width="1.4" rx="3"/>')
    T(x+w/2,y-14,title,13,"middle",600)
    if sub: T(x+w/2,y-30,sub,10,"middle",400,"#555")
    pins={}
    for i,(p,kind,arg) in enumerate(left):
        py=y+20+i*24; T(x+6,py,p,11); L(x-28,py,x,py); pins[p]=(x-28,py)
        if kind=="net": net(x-28,py,arg,"left")
        elif kind=="gnd": L(x-28,py,x-40,py); gnd(x-40,py)
        elif kind=="vcc": L(x-28,py,x-40,py); vcc(x-40,py,arg)
        elif kind=="note": T(x-34,py,arg,10,"end",400,"#555")
    for i,(p,kind,arg) in enumerate(right):
        py=y+20+i*24; T(x+w-6,py,p,11,"end"); L(x+w,py,x+w+28,py); pins[p]=(x+w+28,py)
        if kind=="net": net(x+w+28,py,arg,"right")
        elif kind=="gnd": L(x+w+28,py,x+w+40,py); gnd(x+w+40,py)
        elif kind=="vcc": L(x+w+28,py,x+w+40,py); vcc(x+w+40,py,arg)
    return pins
def res(x,y,horiz=False,label=""):   # 抵抗（長さ40）
    if horiz: o.append(f'<path d="M{x} {y} h8 l3 -6 l6 12 l6 -12 l6 12 l6 -12 l3 6 h2" fill="none" stroke="#000" stroke-width="1.4"/>'); T(x+20,y-14,label,11,"middle")
    else: o.append(f'<path d="M{x} {y} v8 l-6 3 l12 6 l-12 6 l12 6 l-6 3 v8" fill="none" stroke="#000" stroke-width="1.4"/>'); T(x+12,y+20,label,11)
def cap(x,y,label):   # 電解コンデンサ（縦、上が＋）
    L(x,y,x,y+14); L(x-10,y+14,x+10,y+14,2); o.append(f'<path d="M{x-10} {y+22} q10 -5 20 0" fill="none" stroke="#000" stroke-width="2"/>'); L(x,y+20,x,y+34); T(x-14,y+8,"+",11,"middle"); T(x+14,y+18,label,11)
def led(x,y):   # LED（縦、上がアノード）
    o.append(f'<path d="M{x-8} {y} h16 l-8 12 z" fill="none" stroke="#000" stroke-width="1.4"/>'); L(x-8,y+12,x+8,y+12); L(x,y-8,x,y); L(x,y+12,x,y+20)
    o.append(f'<path d="M{x+10} {y+2} l8 -6 M{x+14} {y+8} l8 -6" stroke="#000" stroke-width="1"/>')
W,H=1100,760
o.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><rect width="{W}" height="{H}" fill="white"/>')
T(30,28,"お菓子ディスペンサー 回路図",18,"start",700); T(30,50,"同じ名前の緑のラベルどうしがつながっています。GNDはすべて共通です。",11,"start",400,"#444")
# ESP32-C3
block(470,110,150,"ESP32-C3 SuperMini",
      left=[("GPIO4","net","SCK"),("GPIO5","net","MISO"),("GPIO6","net","MOSI"),("GPIO7","net","SS"),("GPIO10","net","RST"),("GPIO2","net","IR"),("GPIO3","net","BUZ"),("GPIO9","net","DROP")],
      right=[("GPIO0","net","IN1"),("GPIO1","net","IN2"),("GPIO20","net","IN3"),("GPIO21","net","IN4"),("5V","net","5V"),("3V3","net","3V3"),("GND","gnd","")],sub="USBで給電")
# RC522
block(150,110,110,"RC522",sub="ICカード",
      left=[("3.3V","net","3V3"),("GND","gnd","")],
      right=[("SDA","net","SS"),("SCK","net","SCK"),("MOSI","net","MOSI"),("MISO","net","MISO"),("RST","net","RST")])
# 10µF
x=60; net(x,250,"3V3","right"); L(x,250,x,262); cap(x,262,"10µF"); gnd(x,296); T(x,226,"RC522の電源",10,"middle",400,"#555")
# 赤外線受信
block(150,300,110,"HX1838B",sub="赤外線受信",left=[("VCC","net","3V3"),("GND","gnd","")],right=[("DO","net","IR")])
# ブザー
p=block(150,420,110,"パッシブブザー",left=[("−","gnd","")],right=[("S","note","")])
sx,sy=p["S"]; res(sx,sy,True,"150Ω"); L(sx+42,sy,sx+52,sy); net(sx+52,sy,"BUZ","right")
# 障害物検知
block(150,520,110,"障害物検知",sub="出口の筒の横",left=[("＋","net","3V3"),("GND","gnd",""),("EN","note","ジャンパーのまま")],right=[("OUT","net","DROP")])
# ULN2003 ＋ モーター
p=block(830,110,120,"ULN2003",sub="モータードライバ",left=[("IN1","net","IN1"),("IN2","net","IN2"),("IN3","net","IN3"),("IN4","net","IN4")],right=[("＋","net","5V"),("−","gnd","")])
o.append('<rect x="845" y="240" width="90" height="16" fill="none" stroke="#000" stroke-dasharray="3 2"/>'); T(890,248,"白コネクタ",10,"middle",400,"#555")
L(890,256,890,276); o.append('<circle cx="890" cy="300" r="24" fill="none" stroke="#000" stroke-width="1.4"/>'); T(890,300,"M",16,"middle",600); T(924,300,"28BYJ-48",11)
# 470µF
x=1030; net(x,130,"5V","right"); L(x,130,x,142); cap(x,142,"470µF"); gnd(x,176); T(x,202,"モーターの電源",10,"middle",400,"#555")
# スリットのLED
for x,name in((840,"RGB LEDモジュール"),(990,"3色LEDモジュール")):
    net(x,430,"5V","right"); L(x,430,x,440); res(x,440,False,"220Ω"); L(x,480,x,492); led(x,500); gnd(x,520); T(x,560,name,11,"middle",500); T(x,576,"光らせる色の数だけ",10,"middle",400,"#555"); T(x,590,"抵抗を通して5Vへ",10,"middle",400,"#555")
# 注記
for i,s in enumerate(["・RC522、赤外線受信、障害物センサーの電源は3.3V（5Vにつながない）",
                      "・GPIO9は起動時にLOWだと書き込みモードになるので、出口の筒が空の状態で電源を入れる",
                      "・コンデンサは＋側を電源へ。ULN2003の電源は5V（USBのVBUS）",
                      "・LEDはESP32のピンを使わず常時点灯（例：水色＝G＋B）"]): T(30,680+i*18,s,11,"start",400,"#333")
o.append('</svg>'); open("回路図.svg","w").write("\n".join(o))
