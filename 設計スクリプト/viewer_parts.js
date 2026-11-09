import * as T from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { PARTS } from "./parts_data.js";

function start() {
  if (!document.body) return setTimeout(start, 30);
  const $ = (id) => document.getElementById(id);
  if (innerWidth < 700) document.body.classList.add("nolist");
  const view = $("view");
  const R = new T.WebGLRenderer({ antialias: true });
  R.setPixelRatio(Math.min(devicePixelRatio, 2));
  R.setClearColor(0xffffff);
  view.appendChild(R.domElement);
  const S = new T.Scene();
  const C = new T.PerspectiveCamera(35, 1, 1, 5000);
  C.up.set(0, 0, 1);
  const CTL = new OrbitControls(C, R.domElement);
  CTL.enableDamping = true;
  S.add(new T.HemisphereLight(0xffffff, 0x8a8fa0, 1.6));
  const L1 = new T.DirectionalLight(0xffffff, 1.6); L1.position.set(250, -400, 500); S.add(L1);
  const L2 = new T.DirectionalLight(0xffffff, 0.6); L2.position.set(-300, 300, 200); S.add(L2);
  const grid = new T.GridHelper(600, 24, 0xd5d8e0, 0xe8eaef); grid.rotation.x = Math.PI / 2; grid.position.z = -0.5; S.add(grid);

  const b64 = (s, Ty) => { const b = Uint8Array.from(atob(s), (c) => c.charCodeAt(0)); return new Ty(b.buffer); };
  const geom = (v, t) => {
    const g = new T.BufferGeometry();
    g.setAttribute("position", new T.BufferAttribute(b64(v, Float32Array), 3));
    g.setIndex(new T.BufferAttribute(b64(t, Uint32Array), 1));
    const n = g.toNonIndexed(); n.computeVertexNormals(); return n;
  };

  const parts = [];
  for (const p of PARTS) {
    const grp = new T.Group();
    const mat = new T.MeshStandardMaterial({ color: p.color, roughness: 0.65, metalness: p.group === "電子部品" && p.id === "motor" ? 0.5 : 0.05, transparent: true, opacity: 1, polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 1 });
    const g = geom(p.v, p.t);
    const mesh = new T.Mesh(g, mat); mesh.userData.part = p; grp.add(mesh);
    const edgeMat = new T.LineBasicMaterial({ color: 0x1b1d24, transparent: true, opacity: 0.55 });
    const edges = new T.LineSegments(new T.EdgesGeometry(g, 25), edgeMat); grp.add(edges);
    const decoMats = [];
    for (const d of p.deco) {
      const dm = new T.MeshStandardMaterial({ color: d.color, roughness: 0.6, transparent: true, opacity: 1 });
      const m2 = new T.Mesh(geom(d.v, d.t), dm); m2.userData.part = p; grp.add(m2); decoMats.push(dm);
    }
    S.add(grp);
    g.computeBoundingBox();
    parts.push({ p, grp, mesh, mat, edgeMat, decoMats, visible: true, ex: new T.Vector3(...p.ex), base: new T.Color(p.color), bb: g.boundingBox.clone() });
  }

  // ---------- 状態 ----------
  let explode = 0, target = 0, selected = null, hovered = null, labelsOn = false;
  const groupsHidden = new Set();

  // ---------- サイドバー ----------
  const list = $("list");
  const groups = [...new Set(PARTS.map((p) => p.group))];
  const rowOf = new Map();
  for (const gname of groups) {
    const sec = document.createElement("div"); sec.className = "grp";
    const head = document.createElement("label"); head.className = "ghead";
    const cb = document.createElement("input"); cb.type = "checkbox"; cb.checked = true;
    cb.onchange = () => { cb.checked ? groupsHidden.delete(gname) : groupsHidden.add(gname); sec.classList.toggle("off", !cb.checked); refresh(); };
    const cnt = parts.filter((x) => x.p.group === gname).length;
    head.append(cb, document.createTextNode(` ${gname}（${cnt}）`));
    sec.appendChild(head);
    for (const pt of parts.filter((x) => x.p.group === gname)) {
      const row = document.createElement("div"); row.className = "row";
      const sw = document.createElement("span"); sw.className = "sw"; sw.style.background = pt.p.color;
      const nm = document.createElement("span"); nm.className = "nm"; nm.textContent = pt.p.name;
      const eye = document.createElement("button"); eye.className = "eye"; eye.title = "表示／非表示"; eye.textContent = "👁";
      eye.onclick = (e) => { e.stopPropagation(); pt.visible = !pt.visible; row.classList.toggle("hid", !pt.visible); if (!pt.visible && selected === pt) select(null); refresh(); };
      row.append(sw, nm, eye);
      row.onclick = () => select(selected === pt ? null : pt);
      row.onmouseenter = () => { hovered = pt; refresh(); };
      row.onmouseleave = () => { hovered = null; refresh(); };
      sec.appendChild(row); rowOf.set(pt, row);
    }
    list.appendChild(sec);
  }

  // ---------- ラベル ----------
  const labLayer = $("labels");
  for (const pt of parts) {
    const d = document.createElement("div"); d.className = "lab"; d.textContent = pt.p.name;
    d.onclick = () => select(pt);
    labLayer.appendChild(d); pt.lab = d;
  }

  function shown(pt) { return pt.visible && !groupsHidden.has(pt.p.group); }

  function refresh() {
    for (const pt of parts) {
      const vis = shown(pt);
      pt.grp.visible = vis;
      const focus = selected ? selected === pt : true;
      const op = focus ? 1 : 0.12;
      pt.mat.opacity = op; pt.mat.depthWrite = op > 0.5;
      pt.edgeMat.opacity = focus ? 0.55 : 0.06;
      for (const dm of pt.decoMats) { dm.opacity = op; dm.depthWrite = op > 0.5; }
      const c = pt.base.clone();
      if (pt === hovered && pt !== selected) c.lerp(new T.Color(0xffe066), 0.45);
      pt.mat.color.copy(c);
      pt.mat.emissive.set(pt === selected ? 0x332200 : 0x000000);
      rowOf.get(pt).classList.toggle("sel", pt === selected);
    }
    const info = $("info");
    if (selected) {
      const p = selected.p;
      info.innerHTML = `<div class="ititle"><span class="sw" style="background:${p.color}"></span>${p.name}</div>
        <div class="igrp">${p.group}</div>
        <div class="isize">外形 ${p.size[0]} × ${p.size[1]} × ${p.size[2]} mm（幅×奥行×高さ）</div>
        <div class="idesc">${p.desc}</div>
        <div class="ibtn"><button id="only">これだけ表示</button><button id="all">全部表示</button></div>`;
      info.style.display = "block";
      $("only").onclick = () => { for (const pt of parts) { pt.visible = pt === selected; rowOf.get(pt).classList.toggle("hid", !pt.visible); } refresh(); fit(explode); };
      $("all").onclick = () => { showAll(); fit(explode); };
    } else info.style.display = "none";
  }
  function showAll() { for (const pt of parts) { pt.visible = true; rowOf.get(pt).classList.remove("hid"); } refresh(); }

  function select(pt) {
    selected = pt; refresh();
    if (pt) rowOf.get(pt).scrollIntoView({ block: "nearest" });
  }

  // ---------- 操作 ----------
  const sl = $("ex");
  sl.oninput = () => { target = explode = sl.value / 100; anim = false; };
  let anim = false;
  sl.onchange = () => fit(explode);
  $("bOpen").onclick = () => { target = 1; anim = true; fit(1); };
  $("bClose").onclick = () => { target = 0; anim = true; fit(0); };
  $("bShell").onclick = (e) => {
    const g = "外装（MDF）"; const cbs = [...document.querySelectorAll(".ghead input")]; const idx = groups.indexOf(g);
    const on = !groupsHidden.has(g); if (on) groupsHidden.add(g); else groupsHidden.delete(g);
    cbs[idx].checked = !on; cbs[idx].closest(".grp").classList.toggle("off", on);
    e.target.classList.toggle("on", on); refresh(); fit(explode);
  };
  $("bLab").onclick = (e) => { labelsOn = !labelsOn; e.target.classList.toggle("on", labelsOn); };
  $("bReset").onclick = () => { select(null); showAll(); for (const g of [...groupsHidden]) groupsHidden.delete(g); document.querySelectorAll(".ghead input").forEach((c) => { c.checked = true; c.closest(".grp").classList.remove("off"); }); $("bShell").classList.remove("on"); target = 0; anim = true; refresh(); resetView(); };
  $("bList").onclick = () => document.body.classList.toggle("nolist");

  // 見えている部品が全部入るようにカメラの距離と注視点を合わせる（eは分解の割合）
  let camAnim = null;
  function fit(e, dir) {
    const s = e * e * (3 - 2 * e), box = new T.Box3();
    for (const pt of parts) if (shown(pt)) box.union(pt.bb.clone().translate(pt.ex.clone().multiplyScalar(s)));
    if (box.isEmpty()) return;
    const sph = box.getBoundingSphere(new T.Sphere());
    const fov = (C.fov * Math.PI) / 180, fovH = 2 * Math.atan(Math.tan(fov / 2) * C.aspect);
    const dist = (sph.radius * (0.98 - 0.1 * e)) / Math.sin(Math.min(fov, fovH) / 2);
    const d = dir || C.position.clone().sub(CTL.target).normalize();
    camAnim = { t0: performance.now(), fromP: C.position.clone(), fromT: CTL.target.clone(), toT: sph.center.clone(), toP: sph.center.clone().add(d.multiplyScalar(dist)) };
  }
  function resetView() { fit(0, new T.Vector3(380, -520, 330).normalize()); }

  // ---------- マウス ----------
  const ray = new T.Raycaster(), mp = new T.Vector2();
  function pick(ev) {
    const r = R.domElement.getBoundingClientRect();
    mp.set(((ev.clientX - r.left) / r.width) * 2 - 1, -((ev.clientY - r.top) / r.height) * 2 + 1);
    ray.setFromCamera(mp, C);
    const objs = parts.filter((pt) => shown(pt) && (!selected || selected === pt || true)).map((pt) => pt.mesh);
    const hits = ray.intersectObjects(objs, false);
    for (const h of hits) { const pt = parts.find((x) => x.mesh === h.object); if (!selected || pt === selected || pt.mat.opacity > 0.5) return pt; }
    return hits.length ? parts.find((x) => x.mesh === hits[0].object) : null;
  }
  const tip = $("tip");
  R.domElement.addEventListener("pointermove", (ev) => {
    const pt = pick(ev);
    if (pt !== hovered) { hovered = pt; refresh(); }
    if (pt) { tip.style.display = "block"; tip.textContent = pt.p.name; tip.style.left = ev.clientX + 14 + "px"; tip.style.top = ev.clientY + 10 + "px"; }
    else tip.style.display = "none";
  });
  R.domElement.addEventListener("pointerleave", () => { hovered = null; tip.style.display = "none"; refresh(); });
  let downAt = null;
  R.domElement.addEventListener("pointerdown", (ev) => { downAt = [ev.clientX, ev.clientY]; });
  R.domElement.addEventListener("pointerup", (ev) => {
    if (!downAt || Math.hypot(ev.clientX - downAt[0], ev.clientY - downAt[1]) > 5) return;
    const pt = pick(ev); select(pt && pt !== selected ? pt : null);
  });

  // ---------- 描画 ----------
  function size() { const w = view.clientWidth, h = view.clientHeight; R.setSize(w, h); C.aspect = w / h; C.updateProjectionMatrix(); }
  C.position.set(380, -520, 330); new ResizeObserver(size).observe(view); size(); resetView(); camAnim.t0 = -1e9;
  const v3 = new T.Vector3();
  function loop() {
    requestAnimationFrame(loop);
    if (anim) { explode += (target - explode) * 0.12; if (Math.abs(target - explode) < 0.002) { explode = target; anim = false; } sl.value = Math.round(explode * 100); }
    const e = explode * explode * (3 - 2 * explode);
    for (const pt of parts) pt.grp.position.copy(pt.ex).multiplyScalar(e);
    grid.position.z = -0.5 - 128 * e;
    if (camAnim) {
      const k = Math.min(1, (performance.now() - camAnim.t0) / 700), q = k * k * (3 - 2 * k);
      C.position.lerpVectors(camAnim.fromP, camAnim.toP, q); CTL.target.lerpVectors(camAnim.fromT, camAnim.toT, q);
      if (k >= 1) camAnim = null;
    }
    CTL.update(); R.render(S, C);
    const rect = R.domElement.getBoundingClientRect();
    for (const pt of parts) {
      const show = shown(pt) && (labelsOn || pt === selected) && (!selected || pt === selected || labelsOn);
      if (!show) { pt.lab.style.display = "none"; continue; }
      v3.set(...pt.p.c).add(pt.grp.position).project(C);
      if (v3.z > 1) { pt.lab.style.display = "none"; continue; }
      pt.lab.style.display = "block";
      pt.lab.style.left = ((v3.x + 1) / 2) * rect.width + "px";
      pt.lab.style.top = ((1 - v3.y) / 2) * rect.height + "px";
      pt.lab.classList.toggle("lsel", pt === selected);
    }
  }
  refresh(); loop();
}
start();
