# 部品ごとに分けた3Dモデルのデータを作る（v15.pyの寸法をそのまま使う）
import json, base64
src = open("v15.py").read().split("PT['engrave']")[0]
exec(src)
import numpy as np

fpanels = [plate4((-TX,-TY,zt),(TX,-TY,zt),(SQ,FY-SQ,zb),(-SQ,FY-SQ,zb)),
           plate4((-TX,TY,zt),(TX,TY,zt),(SQ,FY+SQ,zb),(-SQ,FY+SQ,zb)),
           plate4((-TX,-TY,zt),(-TX,TY,zt),(-SQ,FY+SQ,zb),(-SQ,FY-SQ,zb)),
           plate4((TX,-TY,zt),(TX,TY,zt),(SQ,FY+SQ,zb),(SQ,FY-SQ,zb))]
tank = [box(-55.7,55.7,-66,-63,zt,168), box(-55.7,55.7,63,66,zt,168),
        box(-55.7,-52.7,-63,63,zt,168), box(52.7,55.7,-63,63,zt,168)]
cl = [box(-WI,-WI+3,-60,63,CL0,SH-3), box(WI-3,WI,-60,63,CL0,SH-3), box(-WI+3,WI-3,63,66,CL0,SH-3)]
ledL, ledR = box(-54,-34,-64.5,-63,30,44), box(34,54,-64.5,-63,30,44)
motor_body = cyl(14,19,0,8+SY,SH-19)+box(-21,21,4+SY,12+SY,SH-1,SH)+cyl(4.5,1.5,0,SY,SH)+(cyl(2.5,9,0,SY,SH+1.5))

EXT, INN, PRN, ELE = "外装（MDF）", "内部（MDF）", "3Dプリント", "電子部品"
# id, 名前, グループ, 色, 分解の移動量(mm), 説明, 形状, [一緒に動く飾り(色)]
P = [
 ("front","正面の板",EXT,"#3d4250",(0,-130,0),"MDF 3mm。引き出しの口と光のスリット付き。裏にRC522とLEDを貼る",mdf[0],[]),
 ("armor","正面アーマー板",EXT,"#2b2f3a",(0,-165,0),"MDF 3mm。正面の板に接着。八角形の窓がICカードをかざす場所",armor,[(a_e,"#c9a27a")]),
 ("back","背面の板",EXT,"#3d4250",(0,130,0),"MDF 3mm。ハニカム穴と下にUSBケーブルの穴",mdf[1],[]),
 ("sideL","側面（左）",EXT,"#4a5060",(-130,0,0),"MDF 3mm。ハニカム穴",mdf[3],[]),
 ("sideR","側面（右）",EXT,"#4a5060",(130,0,0),"MDF 3mm。ハニカム穴",mdf[4],[]),
 ("bottom","底板",EXT,"#353a46",(0,0,-120),"MDF 3mm。全体の土台",mdf[2],[]),
 ("chLowL","下の斜め板（左）",EXT,"#5a6072",(-130,0,-50),"MDF 3mm。底の角を斜めに切った板",mdf[5],[]),
 ("chLowR","下の斜め板（右）",EXT,"#5a6072",(130,0,-50),"MDF 3mm。底の角を斜めに切った板",mdf[6],[]),
 ("chTopL","上の斜め板（左）",EXT,"#5a6072",(-115,0,140),"MDF 3mm。上の角を斜めに切った板",mdf[7],[]),
 ("chTopR","上の斜め板（右）",EXT,"#5a6072",(115,0,140),"MDF 3mm。上の角を斜めに切った板",mdf[8],[]),
 ("lid","天板",EXT,"#353a46",(0,0,205),"MDF 3mm。中央が補充口",PT["lid"],[]),
 ("hatch","補充口のフタ",EXT,"#ff2bd6",(0,0,245),"MDF 3mm。指をかける穴付き。上にのせるだけ",PT["hatch"],[]),

 ("shelf","中棚",INN,"#d2ab78",(0,0,0),"MDF 3mm。回転部（base・モーター・センサー筒）をネジでとめる板。受け木とリブの上にのせて接着",mdf[9],[]),
 ("cleatL","受け木（左）",INN,"#b8915c",(-70,0,-35),"MDF 3mm、123×10。中棚のすぐ下で側面の内側に接着",cl[0],[]),
 ("cleatR","受け木（右）",INN,"#b8915c",(70,0,-35),"MDF 3mm、123×10。中棚のすぐ下で側面の内側に接着",cl[1],[]),
 ("cleatB","受け木（後ろ）",INN,"#b8915c",(0,70,-35),"MDF 3mm、105.4×10。中棚のすぐ下で背面の内側に接着",cl[2],[]),
 ("rib","縦リブ",INN,"#a37d4a",(0,40,-60),"MDF 3mm、60×42。モーターの後ろで底板と中棚をつなぐ柱。下の切り欠きに配線を通す",rib,[]),
 ("tankF","内箱（前）",INN,"#e0bf8f",(0,-55,150),"MDF 3mm、111.4×18。外壁の内側に接着",tank[0],[]),
 ("tankB","内箱（後ろ）",INN,"#e0bf8f",(0,55,150),"MDF 3mm、111.4×18。外壁の内側に接着",tank[1],[]),
 ("tankL","内箱（左）",INN,"#d6b07c",(-55,0,150),"MDF 3mm、126×18。前後の板の間にはさんで外壁に接着",tank[2],[]),
 ("tankR","内箱（右）",INN,"#d6b07c",(55,0,150),"MDF 3mm、126×18。前後の板の間にはさんで外壁に接着",tank[3],[]),
 ("funF","じょうご（前）",INN,"#f0d2a3",(0,-35,105),"MDF 3mm。上の端を内箱に接着、下の口は変換口にのる",fpanels[0],[]),
 ("funB","じょうご（後ろ）",INN,"#f0d2a3",(0,35,105),"MDF 3mm。上の端を内箱に接着",fpanels[1],[]),
 ("funL","じょうご（左）",INN,"#e6c48f",(-35,0,105),"MDF 3mm。上の端を内箱に接着",fpanels[2],[]),
 ("funR","じょうご（右）",INN,"#e6c48f",(35,0,105),"MDF 3mm。上の端を内箱に接着",fpanels[3],[]),
 ("drawer","引き出し",INN,"#c39a62",(0,-175,-75),"MDF 3mm（底・前後・左右の5枚）。出てきたお菓子を受ける",PT["mdf_drawer"],[]),
 ("dface","引き出しの前板",INN,"#2b2f3a",(0,-205,-75),"MDF 3mm。指をかける穴とシェブロンの刻印",PT["drawer_face"],[(dfe,"#c9a27a")]),
 ("rails","引き出しのレール（2本）",INN,"#8a6a40",(0,0,-100),"MDF 3mm、56×5。底板に接着",PT["rails"],[]),

 ("base","base（円盤の受け皿）",PRN,"#4f8fe0",(0,0,30),"3Dプリント Φ102×21。円盤はこの床に直接のって回る。裏にモーター、中棚へM3ネジ3本",PT["base"],[]),
 ("disc","disc（回転円盤）",PRN,"#f39c12",(0,0,62),"3Dプリント Φ80、穴Φ24×4。1穴＝1杯＝M&M約5粒。モーター軸のD形に差し込む",PT["disc"],[]),
 ("adapter","adapter（変換口）",PRN,"#2ecc71",(0,0,92),"3Dプリント Φ91。じょうごの四角い口を円盤の穴へつなぐ。ピン3本で位置決め",PT["adapter"],[]),
 ("tube","sensor_tube（センサー筒）",PRN,"#1abc9c",(0,-25,-45),"3Dプリント。出口の下の筒。横の台に障害物センサーをのせ、窓から落ちるお菓子を見る",PT["sensor_tube"],[]),

 ("motor","ステッピングモーター 28BYJ-48",ELE,"#b8bcc6",(0,0,-45),"5V。baseの裏にM3ネジ2本。軸が円盤を回す",motor_body,[]),
 ("uln","ULN2003ドライバ",ELE,"#1e8449",(0,85,20),"モーターを動かす基板。背面の内側に貼る",PT["uln2003"],[]),
 ("esp","ESP32-C3 SuperMini",ELE,"#1f5fbf",(40,70,-85),"マイコン。底板の後ろ側に貼る",PT["esp32"],[]),
 ("buzzer","パッシブブザー",ELE,"#222222",(-40,70,-85),"音で知らせる。底板の後ろ側に貼る",PT["buzzer"],[]),
 ("rc522","RC522（ICカードリーダー）",ELE,"#2f80ed",(0,-95,0),"正面の板の裏に貼る。アーマー板の窓にカードをかざす",PT["rc522"],[]),
 ("ledL","LEDモジュール（左）",ELE,"#00e5ff",(-20,-95,0),"中棚の下、左のスリットの裏に貼る。常時点灯",ledL,[]),
 ("ledR","LEDモジュール（右）",ELE,"#ff4fd8",(20,-95,0),"中棚の下、右のスリットの裏に貼る。常時点灯",ledR,[]),
 ("sensor","障害物センサー",ELE,"#27ae60",(0,-25,-45),"センサー筒の台にのせる。お菓子が落ちたかを見る",PT["sensor"],[]),
]

def pack(m):
    g = m.to_mesh(); v = np.asarray(g.vert_properties[:, :3], np.float32); t = np.asarray(g.tri_verts, np.uint32)
    return base64.b64encode(v.tobytes()).decode(), base64.b64encode(t.tobytes()).decode(), v

out = []
for pid, name, grp, col_, ex, desc, m, deco in P:
    vb, tb, v = pack(m)
    lo, hi = v.min(0), v.max(0)
    d = {"id": pid, "name": name, "group": grp, "color": col_, "ex": ex, "desc": desc, "v": vb, "t": tb,
         "size": [round(float(x), 1) for x in (hi - lo)], "c": [round(float(x), 1) for x in (lo + hi) / 2], "deco": []}
    for dm, dc in deco:
        if dm.bounding_box()[3] > 400: continue
        a, b, _ = pack(dm); d["deco"].append({"v": a, "t": b, "color": dc})
    out.append(d)
    print(pid, d["size"])
open("parts_data.js", "w").write("export const PARTS=" + json.dumps(out, ensure_ascii=False) + ";")
print(len(out), "parts")
