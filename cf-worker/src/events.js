// 事件自动发现：从实时采集里挑出“喜马拉雅上游突发事件”的公开信号，合并成事件，交给 GitHub 生成证据包。
// 只记录公开来源说了什么、什么时候说的；不判断成因，不预测，不发布预警。
// 规则：
//   - BIPAD 洪水警报（hazard 11）且发生在喜马拉雅山区县 → 同一县同一天合并为一个事件
//   - USGS 归类为 landslide（崩塌/滑坡）的事件
//   - GDACS 橙色/红色级别、在喜马拉雅范围内的事件
//   - 本平台监测的水位站在报且越过警戒线

// 喜马拉雅高山区县（尼泊尔，有冰川或跨境上游河流）大致中心，用于没有坐标的警报
export const DISTRICTS = {
  Taplejung: [27.62, 87.78], Sankhuwasabha: [27.6, 87.3], Solukhumbu: [27.79, 86.66], Dolakha: [27.78, 86.17], Sindhupalchok: [27.95, 85.69],
  Sindhupalchowk: [27.95, 85.69], Rasuwa: [28.11, 85.3], Nuwakot: [27.92, 85.17], Dhading: [27.87, 84.92], Gorkha: [28.3, 84.63], Lamjung: [28.27, 84.36],
  Manang: [28.67, 84.02], Mustang: [28.98, 83.87], Myagdi: [28.6, 83.5], Kaski: [28.32, 83.97], 
  Dolpa: [29.0, 82.87], Mugu: [29.55, 82.15], Jumla: [29.27, 82.18], Humla: [30.0, 81.8], Kalikot: [29.15, 81.62], Bajura: [29.5, 81.5],
  Bajhang: [29.7, 81.2], Darchula: [29.85, 80.75], 
  Ramechhap: [27.5, 86.08], 
};
const BOX = { s: 26.5, n: 31.5, w: 79.5, e: 92.5 };
const inBox = (lat, lon) => lat != null && lon != null && lat >= BOX.s && lat <= BOX.n && lon >= BOX.w && lon <= BOX.e;
const npDay = s => new Date(Date.parse(s) + 345 * 60e3).toISOString().slice(0, 10);   // 尼泊尔日期
const districtOf = title => { const m = /,\s*([^,]+?)\s*$/.exec(title || ""); if (!m) return null; const d = m[1].trim(); return DISTRICTS[d] ? d : null; };

export function detect(rt, prev) {
  const S = (rt && rt.sources) || {}, v = k => (S[k] || {}).v || {}, ev = Object.assign({}, prev || {});
  const add = (id, base, item) => {
    const e = ev[id] || Object.assign({ id, first_seen: new Date().toISOString(), src: [] }, base);
    if (!e.src.some(x => x.k === item.k || (x.src === item.src && x.t === item.t))) { e.src.push(item); e.src.sort((a, b) => a.t.localeCompare(b.t)); e.updated = new Date().toISOString(); }
    if (item.t < e.t) e.t = item.t;
    ev[id] = e;
  };
  for (const a of v("alerts").alerts || []) {
    if (a.hazard !== 11 && !/flood/i.test(a.title || "")) continue;
    const d = districtOf(a.title), pt = a.lat != null ? [a.lat, a.lon] : d ? DISTRICTS[d] : null;
    if (!pt || !inBox(pt[0], pt[1]) || !d) continue;
    const t = new Date(a.started).toISOString();
    add(`bipad-${d.toLowerCase().replace(/\s+/g, "-")}-${npDay(a.started)}`, { kind: "洪水", title: `${d} 洪水预警`, title_en: `${d} flood warning`, place: (a.title || "").replace(/^Flood warning at\s*/i, ""), lat: pt[0], lon: pt[1], t },
      { k: "bipad:" + (a.id || a.started), t, src: "BIPAD 灾害警报", text: a.title + (a.expire ? "（已结束）" : ""), text_en: a.title + (a.expire ? " (ended)" : "") });
  }
  for (const q of v("usgs").events || []) {
    if (q.type !== "landslide" || !inBox(q.lat, q.lon)) continue;
    add(`usgs-${q.id}`, { kind: "崩塌", title: `USGS 记录的崩塌/滑坡 M${q.mag}`, title_en: `Landslide/collapse recorded by USGS, M${q.mag}`, place: q.place, lat: q.lat, lon: q.lon, t: q.t },
      { k: "usgs:" + q.id, t: q.t, src: "USGS 地震目录", text: `M${q.mag} 归类为崩塌/滑坡（非构造）· ${q.place}`, text_en: `M${q.mag} classified as landslide/collapse (non-tectonic) · ${q.place}`, url: q.url });
  }
  for (const g of v("gdacs").events || []) {
    if (!/orange|red/i.test(g.level || "") || !inBox(g.lat, g.lon)) continue;
    const t = new Date(g.from + (/[zZ+]/.test(g.from || "") ? "" : "Z")).toISOString();
    add(`gdacs-${g.type}-${(g.from || "").slice(0, 10)}`, { kind: g.type === "FL" ? "洪水" : g.type, title: g.name, title_en: g.name, place: g.name, lat: g.lat, lon: g.lon, t },
      { k: "gdacs:" + g.type + g.from, t, src: "GDACS", text: `${g.level} 级 · ${g.name}`, text_en: `${g.level} alert · ${g.name}`, url: g.url });
  }
  for (const [id, s] of Object.entries(v("bipad").st || {})) {
    const m = s.meta || {}, now = Date.parse(rt.updated);
    if (!m.status || /BELOW/.test(m.status) || !m.last_on || now - Date.parse(m.last_on) > 6 * 3600e3) continue;
    const t = new Date(m.last_on).toISOString();
    add(`gauge-${id}-${npDay(m.last_on)}`, { kind: "水位越线", title: `${m.name} 越过${/DANGER/.test(m.status) ? "危险" : "警戒"}水位`, title_en: `${m.title} ${/DANGER/.test(m.status) ? "above danger level" : "above warning level"}`, place: m.title, lat: m.lat, lon: m.lon, t },
      { k: "gauge:" + id + ":" + t, t, src: "BIPAD 水位站", text: `${m.name} ${m.status}`, text_en: `${m.title} ${m.status}` });
  }
  // 清掉同一来源同一时刻的重复（旧版本用时间做键，新版本用警报编号做键）
  for (const e of Object.values(ev)) { const seen = new Set(); e.src = e.src.filter(x => { const k = x.src + "|" + x.t; if (seen.has(k)) return false; seen.add(k); return true; }); }
  // 同一事件的不同来源合并：时间相差 36 小时内、距离 150 km 内的并到最早的那个
  const km = (a, b) => { const r = Math.PI / 180, x = Math.sin((b.lat - a.lat) * r / 2) ** 2 + Math.cos(a.lat * r) * Math.cos(b.lat * r) * Math.sin((b.lon - a.lon) * r / 2) ** 2; return 12742 * Math.asin(Math.sqrt(x)); };
  const L = Object.values(ev).sort((a, b) => a.t.localeCompare(b.t));
  for (let i = 0; i < L.length; i++) for (let j = i + 1; j < L.length; j++) {
    const A = L[i], B = L[j]; if (!ev[A.id] || !ev[B.id]) continue;
    if (Math.abs(Date.parse(B.t) - Date.parse(A.t)) < 36 * 3600e3 && km(A, B) < 150) {
      for (const it of B.src) if (!A.src.some(x => x.k === it.k || (x.src === it.src && x.t === it.t))) A.src.push(it);
      A.src.sort((a, b) => a.t.localeCompare(b.t)); A.also = (A.also || []).concat([B.id], B.also || []);
      if (A.kind !== B.kind && !String(A.kind).includes(B.kind)) A.kind = A.kind + "、" + B.kind;
      delete ev[B.id];
    }
  }
  // 合并过的事件，以后新来的同源信号也并进来
  for (const e of Object.values(ev)) for (const o of e.also || []) if (ev[o]) { for (const it of ev[o].src) if (!e.src.some(x => x.k === it.k)) e.src.push(it); delete ev[o]; }
  // 只保留 60 天
  for (const k of Object.keys(ev)) if (Date.now() - Date.parse(ev[k].t) > 60 * 864e5) delete ev[k];
  return ev;
}

// 证据包由 GitHub 工作流 evidence（events 分支）生成。新事件或有新信号时立刻触发；有 14 天内的事件时每 6 小时补一次（补卫星“事后”影像）。
export async function kick(env, events, lastKick, sig) {
  if (!env.GH_TOKEN || !env.GH_REPO) return { skip: "没有 GH_TOKEN" };
  const recent = Object.values(events).some(e => Date.now() - Date.parse(e.t) < 14 * 864e5);
  const due = sig !== (lastKick && lastKick.sig) || (recent && Date.now() - Date.parse((lastKick && lastKick.at) || 0) > 6 * 3600e3);
  if (!due) return null;
  const H = { "user-agent": "everest-facets-worker", accept: "application/vnd.github+json", authorization: "Bearer " + env.GH_TOKEN };
  const cur = await fetch(`https://api.github.com/repos/${env.GH_REPO}/contents/trigger.txt?ref=events`, { headers: H });
  const sha = cur.ok ? (await cur.json()).sha : undefined;
  const now = new Date().toISOString();
  const put = await fetch(`https://api.github.com/repos/${env.GH_REPO}/contents/trigger.txt`, { method: "PUT", headers: { ...H, "content-type": "application/json" },
    body: JSON.stringify({ message: "evidence trigger " + now, content: btoa(now + "\n" + sig + "\n"), branch: "events", sha }) });
  return { at: now, sig, status: put.status };
}
