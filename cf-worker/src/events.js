// 事件自动发现：从实时采集里挑出“喜马拉雅上游突发事件”的公开信号，合并成事件，交给 GitHub 生成证据包。
// 只记录公开来源说了什么、什么时候说的；不判断成因，不预测，不发布预警。
// 规则：
//   - BIPAD 洪水警报（hazard 11）且发生在喜马拉雅山区县 → 同一县同一天合并为一个事件
//   - USGS 归类为 landslide（崩塌/滑坡）的事件
//   - GDACS 橙色/红色级别、在喜马拉雅范围内的事件
//   - 本平台监测的水位站在报且越过警戒线
//   - 新闻线索（GDELT）：标题里同时有灾种（雪崩、冰湖溃决、泥石流、滑坡、暴雪、洪水）和喜马拉雅地名，同一天至少两家媒体

// 喜马拉雅高山区县（尼泊尔，有冰川或跨境上游河流）大致中心，用于没有坐标的警报
export const DISTRICTS = {
  Taplejung: [27.62, 87.78], Sankhuwasabha: [27.6, 87.3], Solukhumbu: [27.79, 86.66], Dolakha: [27.78, 86.17], Sindhupalchok: [27.95, 85.69],
  Sindhupalchowk: [27.95, 85.69], Rasuwa: [28.11, 85.3], Nuwakot: [27.92, 85.17], Dhading: [27.87, 84.92], Gorkha: [28.3, 84.63], Lamjung: [28.27, 84.36],
  Manang: [28.67, 84.02], Mustang: [28.98, 83.87], Myagdi: [28.6, 83.5], Kaski: [28.32, 83.97], 
  Dolpa: [29.0, 82.87], Mugu: [29.55, 82.15], Jumla: [29.27, 82.18], Humla: [30.0, 81.8], Kalikot: [29.15, 81.62], Bajura: [29.5, 81.5],
  Bajhang: [29.7, 81.2], Darchula: [29.85, 80.75], 
  Ramechhap: [27.5, 86.08], 
};
// 新闻里常见的山峰、山谷和西藏一侧地名
const PLACES = Object.assign({}, DISTRICTS, { Everest: [27.99, 86.93], Khumbu: [27.95, 86.8], Lukla: [27.69, 86.73], Namche: [27.8, 86.71], Manaslu: [28.55, 84.56],
  Annapurna: [28.6, 83.82], Langtang: [28.21, 85.56], Dhaulagiri: [28.7, 83.49], Makalu: [27.89, 87.09], Kanchenjunga: [27.7, 88.15], Kangchenjunga: [27.7, 88.15],
  Rolwaling: [27.88, 86.4], Melamchi: [27.83, 85.58], Tingri: [28.66, 87.12], Dingri: [28.66, 87.12], Gyirong: [28.85, 85.3], Kyirong: [28.85, 85.3],
  Nyalam: [28.16, 85.98], Zhangmu: [27.99, 85.98], Rasuwagadhi: [28.27, 85.38], Tatopani: [27.95, 85.94] });
// 新闻灾种 → [正则, 中文, 英文, UNDRR-ISC 2025 灾害编码]（顺序即优先级）
const NEWS_KIND = [[/glacial lake|GLOF/i, "冰湖溃决", "glacial lake outburst", "MH0607"], [/ice avalanche|rockfall|rock fall/i, "崩落", "rockfall / ice avalanche", "GH0301"],
  [/avalanche/i, "雪崩", "avalanche", "MH0801"], [/debris flow|mudflow/i, "泥石流", "debris flow", "GH0303"], [/landslide/i, "滑坡", "landslide", "GH0300"],
  [/dam (breach|burst|collapse|failure)/i, "溃坝", "dam failure", "TL0205"], [/flash flood/i, "山洪", "flash flood", "MH0603"], [/flood/i, "洪水", "flood", "MH0600"],
  [/blizzard/i, "暴风雪", "blizzard", "MH0403"], [/snowstorm|heavy snow/i, "雪暴", "snowstorm", "MH0406"], [/hailstorm|hail/i, "冰雹", "hail", "MH0404"],
  [/lightning/i, "雷击", "lightning", "MH0102"], [/cold wave/i, "寒潮", "cold wave", "MH0502"], [/forest fire|wildfire/i, "森林火灾", "wildfire", "EN0205"],
  [/earthquake|quake/i, "地震", "earthquake", "GH0101"], [/cholera/i, "霍乱", "cholera", "BI0204"], [/dengue/i, "登革热", "dengue", "BI0207"], [/outbreak/i, "疫情", "outbreak", "BI0110"]];
// BIPAD 警报标题 → 灾种（只取已经发生的灾害；“Heavy Rainfall”这类预报性警报不建事件）
const BIPAD_KIND = [[/flood/i, "洪水", "flood", "MH0604"], [/landslide/i, "滑坡", "landslide", "GH0300"], [/avalanche/i, "雪崩", "avalanche", "MH0801"],
  [/forest fire|wildfire/i, "森林火灾", "forest fire", "EN0205"], [/lightning|thunderbolt/i, "雷击", "lightning", "MH0102"], [/cold wave/i, "寒潮", "cold wave", "MH0502"],
  [/snow/i, "降雪", "snowfall", "MH0405"], [/earthquake/i, "地震", "earthquake", "GH0101"]];
const GDACS_HIPS = { EQ: "GH0101", FL: "MH0600", TC: "MH0309", DR: "MH0401", WF: "EN0205", VO: "GH0200" };
const GDACS_ZH = { EQ: "地震", FL: "洪水", TC: "热带气旋", DR: "干旱", WF: "野火", VO: "火山" };
const BOX = { s: 26.5, n: 31.5, w: 79.5, e: 92.5 };
const inBox = (lat, lon) => lat != null && lon != null && lat >= BOX.s && lat <= BOX.n && lon >= BOX.w && lon <= BOX.e;
const npDay = s => new Date(Date.parse(s) + 345 * 60e3).toISOString().slice(0, 10);   // 尼泊尔日期
const districtOf = title => { const m = /,\s*([^,]+?)\s*$/.exec(title || ""); if (!m) return null; const d = m[1].trim(); return DISTRICTS[d] ? d : null; };

export function detect(rt, prev) {
  const S = (rt && rt.sources) || {}, v = k => (S[k] || {}).v || {}, ev = Object.assign({}, prev || {});
  const add = (id, base, item) => {
    const e = ev[id] || Object.assign({ id, first_seen: new Date().toISOString(), src: [] }, base);
    e.hips = [...new Set([...(e.hips || []), ...(base.hips || [])])];
    if (!e.src.some(x => x.k === item.k || (x.src === item.src && x.t === item.t))) { e.src.push(item); e.src.sort((a, b) => a.t.localeCompare(b.t)); e.updated = new Date().toISOString(); }
    if (item.t < e.t) e.t = item.t;
    ev[id] = e;
  };
  for (const a of v("alerts").alerts || []) {
    const bk = a.hazard === 11 ? BIPAD_KIND[0] : BIPAD_KIND.find(k => k[0].test(a.title || "")); if (!bk) continue;
    const d = districtOf(a.title), pt = a.lat != null ? [a.lat, a.lon] : d ? DISTRICTS[d] : null;
    if (!pt || !inBox(pt[0], pt[1]) || !d) continue;
    const t = new Date(a.started).toISOString();
    add(`bipad-${d.toLowerCase().replace(/\s+/g, "-")}-${npDay(a.started)}` + (bk[3] === "MH0604" ? "" : "-" + bk[2].replace(/\s+/g, "-")),
      { kind: bk[1], hips: [bk[3]], title: `${d} ${bk[1]}${bk[3] === "MH0604" ? "预警" : "警报"}`, title_en: `${d} ${bk[2]} ${bk[3] === "MH0604" ? "warning" : "alert"}`, place: (a.title || "").replace(/^.*?\bat\s+/i, ""), lat: pt[0], lon: pt[1], t },
      { k: "bipad:" + (a.id || a.started), t, src: "BIPAD 灾害警报", text: a.title + (a.expire ? "（已结束）" : ""), text_en: a.title + (a.expire ? " (ended)" : "") });
  }
  for (const q of v("usgs").events || []) {
    if (!inBox(q.lat, q.lon)) continue;
    if (q.type !== "landslide") {   // 构造地震：只收 M5 以上
      if (!(q.mag >= 5)) continue;
      add(`usgs-${q.id}`, { kind: "地震", hips: ["GH0101"], title: `M${q.mag} 地震`, title_en: `M${q.mag} earthquake`, place: q.place, lat: q.lat, lon: q.lon, t: q.t },
        { k: "usgs:" + q.id, t: q.t, src: "USGS 地震目录", text: `M${q.mag} 地震 · ${q.place}`, text_en: `M${q.mag} earthquake · ${q.place}`, url: q.url });
      continue;
    }
    add(`usgs-${q.id}`, { kind: "崩塌", hips: ["GH0300"], title: `USGS 记录的崩塌/滑坡 M${q.mag}`, title_en: `Landslide/collapse recorded by USGS, M${q.mag}`, place: q.place, lat: q.lat, lon: q.lon, t: q.t },
      { k: "usgs:" + q.id, t: q.t, src: "USGS 地震目录", text: `M${q.mag} 归类为崩塌/滑坡（非构造）· ${q.place}`, text_en: `M${q.mag} classified as landslide/collapse (non-tectonic) · ${q.place}`, url: q.url });
  }
  for (const g of v("gdacs").events || []) {
    if (!/orange|red/i.test(g.level || "") || !inBox(g.lat, g.lon)) continue;
    const t = new Date(g.from + (/[zZ+]/.test(g.from || "") ? "" : "Z")).toISOString();
    add(`gdacs-${g.type}-${(g.from || "").slice(0, 10)}`, { kind: GDACS_ZH[g.type] || g.type, hips: GDACS_HIPS[g.type] ? [GDACS_HIPS[g.type]] : [], title: g.name, title_en: g.name, place: g.name, lat: g.lat, lon: g.lon, t },
      { k: "gdacs:" + g.type + g.from, t, src: "GDACS", text: `${g.level} 级 · ${g.name}`, text_en: `${g.level} alert · ${g.name}`, url: g.url });
  }
  for (const [id, s] of Object.entries(v("bipad").st || {})) {
    const m = s.meta || {}, now = Date.parse(rt.updated);
    if (!m.status || /BELOW/.test(m.status) || !m.last_on || now - Date.parse(m.last_on) > 6 * 3600e3) continue;
    const t = new Date(m.last_on).toISOString();
    add(`gauge-${id}-${npDay(m.last_on)}`, { kind: "水位越线", hips: ["MH0604"], title: `${m.name} 越过${/DANGER/.test(m.status) ? "危险" : "警戒"}水位`, title_en: `${m.title} ${/DANGER/.test(m.status) ? "above danger level" : "above warning level"}`, place: m.title, lat: m.lat, lon: m.lon, t },
      { k: "gauge:" + id + ":" + t, t, src: "BIPAD 水位站", text: `${m.name} ${m.status}`, text_en: `${m.title} ${m.status}` });
  }
  const grp = {};
  for (const a of v("news").arts || []) {
    const kk = NEWS_KIND.find(k => k[0].test(a.title)); if (!kk) continue;
    const pl = Object.keys(PLACES).find(p => new RegExp("\\b" + p + "\\b", "i").test(a.title)); if (!pl) continue;
    const key = `${kk[2]}|${pl}|${npDay(a.t)}`; (grp[key] = grp[key] || { kk, pl, arts: [] }).arts.push(a);
  }
  for (const [key, g] of Object.entries(grp)) {
    if (new Set(g.arts.map(a => a.domain)).size < 2) continue;
    const t = g.arts.map(a => a.t).sort()[0], [la, lo] = PLACES[g.pl];
    for (const a of g.arts) add(`news-${g.kk[2].replace(/\s+/g, "-")}-${g.pl.toLowerCase()}-${key.split("|")[2]}`,
      { kind: g.kk[1], hips: [g.kk[3]], title: `${g.pl} ${g.kk[1]}（新闻线索）`, title_en: `${g.pl} ${g.kk[2]} (news lead)`, place: g.pl, lat: la, lon: lo, t },
      { k: "news:" + a.url, t: a.t, src: "新闻（GDELT）", text: `${a.domain}：${a.title}`, text_en: `${a.domain}: ${a.title}`, url: a.url });
  }
  // 清掉同一来源同一时刻的重复（旧版本用时间做键，新版本用警报编号做键）
  for (const e of Object.values(ev)) { const seen = new Set(); e.src = e.src.filter(x => { const k = x.src + "|" + x.t; if (seen.has(k)) return false; seen.add(k); return true; }); }
  // 同一事件的不同来源合并：时间相差 36 小时内、距离 150 km 内的并到最早的那个
  const km = (a, b) => { const r = Math.PI / 180, x = Math.sin((b.lat - a.lat) * r / 2) ** 2 + Math.cos(a.lat * r) * Math.cos(b.lat * r) * Math.sin((b.lon - a.lon) * r / 2) ** 2; return 12742 * Math.asin(Math.sqrt(x)); };
  const L = Object.values(ev).sort((a, b) => a.t.localeCompare(b.t));
  for (let i = 0; i < L.length; i++) for (let j = i + 1; j < L.length; j++) {
    const A = L[i], B = L[j]; if (!ev[A.id] || !ev[B.id]) continue;
    const bio = E => (E.hips || []).some(c => c.startsWith("BI"));
    if (bio(A) !== bio(B)) continue;   // 疫情和自然灾害不合并
    if (Math.abs(Date.parse(B.t) - Date.parse(A.t)) < 36 * 3600e3 && km(A, B) < 150) {
      for (const it of B.src) if (!A.src.some(x => x.k === it.k || (x.src === it.src && x.t === it.t))) A.src.push(it);
      A.src.sort((a, b) => a.t.localeCompare(b.t)); A.also = [...new Set([...(A.also || []), B.id, ...(B.also || [])])]; A.hips = [...new Set([...(A.hips || []), ...(B.hips || [])])];
      if (A.kind !== B.kind && !String(A.kind).includes(B.kind)) A.kind = A.kind + "、" + B.kind;
      delete ev[B.id];
    }
  }
  // 合并过的事件，以后新来的同源信号也并进来
  for (const e of Object.values(ev)) for (const o of e.also || []) if (ev[o]) { for (const it of ev[o].src) if (!e.src.some(x => x.k === it.k)) e.src.push(it); delete ev[o]; }
  for (const e of Object.values(ev)) if (e.also) e.also = [...new Set(e.also)];   // 清掉旧版本重复累积的合并记录
  // 旧事件补灾害编码（UNDRR-ISC 2025）
  for (const e of Object.values(ev)) if (!e.hips || !e.hips.length)
    e.hips = /^gdacs-(\w+)-/.test(e.id) ? [GDACS_HIPS[e.id.split("-")[1]] || "MH0600"] : /^usgs-/.test(e.id) ? [e.kind === "地震" ? "GH0101" : "GH0300"] : ["MH0604"];
  // 只保留 60 天
  for (const k of Object.keys(ev)) if (Date.now() - Date.parse(ev[k].t) > 60 * 864e5) delete ev[k];
  return ev;
}

// 证据包由 GitHub 工作流 evidence（events 分支）生成。新事件或有新信号时立刻触发；有 14 天内的事件时每小时补一次（取新的卫星影像、扫描记录、存证确认）（补卫星“事后”影像）。
export async function kick(env, events, lastKick, sig) {
  if (!env.GH_TOKEN || !env.GH_REPO) return { skip: "没有 GH_TOKEN" };
  const recent = Object.values(events).some(e => Date.now() - Date.parse(e.t) < 14 * 864e5);
  const due = sig !== (lastKick && lastKick.sig) || (recent && Date.now() - Date.parse((lastKick && lastKick.at) || 0) > 3600e3);
  if (!due) return null;
  const H = { "user-agent": "everest-facets-worker", accept: "application/vnd.github+json", authorization: "Bearer " + env.GH_TOKEN };
  const cur = await fetch(`https://api.github.com/repos/${env.GH_REPO}/contents/trigger.txt?ref=events`, { headers: H });
  const sha = cur.ok ? (await cur.json()).sha : undefined;
  const now = new Date().toISOString();
  const put = await fetch(`https://api.github.com/repos/${env.GH_REPO}/contents/trigger.txt`, { method: "PUT", headers: { ...H, "content-type": "application/json" },
    body: JSON.stringify({ message: "evidence trigger " + now, content: btoa(now + "\n" + sig + "\n"), branch: "events", sha }) });
  return { at: now, sig, status: put.status };
}


// GitHub 的定时任务（cron）常常延迟甚至几小时不跑。灾种扫描要“实时”，改由 Worker 每小时触发：
// 改 events 分支的 hazards/tick.txt（和证据包的 trigger.txt 同一种做法，只需要内容写权限）→ events 分支的 hazards-tick 工作流
// 用 GITHUB_TOKEN 启动 main 上的 hazards 工作流。每天 02:40 以后第一次是期刊排名（venues），其余是扫描（scan）。
export async function hazardsKick(env, last) {
  if (!env.GH_TOKEN || !env.GH_REPO) return { skip: "没有 GH_TOKEN" };
  const now = new Date(), L = last || {};
  const due = (t, ms) => !t || now - Date.parse(t) >= ms;
  let task = null;
  if (now.getUTCHours() === 2 && now.getUTCMinutes() >= 40 && due(L.venues_at, 20 * 3600e3)) task = "venues";
  else if (due(L.insar_at, 6 * 3600e3)) task = "insar";   // v78：InSAR 每日管线每 6 小时一次（GitHub 自带定时每天只跑约 2 次）
  else if (due(L.scan_at, 20 * 60e3)) task = "scan";
  // v76：每 20 分钟扫一次（原来每小时），扫描约 6–10 分钟；总览页通过连接器 everest_hazard_records 直接读结果，不等同步任务
  if (!task) return null;
  const H = { "user-agent": "everest-facets-worker", accept: "application/vnd.github+json", authorization: "Bearer " + env.GH_TOKEN };
  const path = `https://api.github.com/repos/${env.GH_REPO}/contents/hazards/tick.txt`;
  const cur = await fetch(path + "?ref=events", { headers: H });
  const sha = cur.ok ? (await cur.json()).sha : undefined;
  const r = await fetch(path, { method: "PUT", headers: { ...H, "content-type": "application/json" },
    body: JSON.stringify({ message: `hazards ${task} tick ${now.toISOString()}`, content: btoa(task + "\n" + now.toISOString() + "\n"), branch: "events", sha }) });
  // 成功是 200/201；失败也记时间（避免每 5 分钟重复请求），状态码留着排查
  return { ...L, [task + "_status"]: r.status, [task + "_at"]: now.toISOString() };
}
