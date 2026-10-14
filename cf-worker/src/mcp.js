// EVEREST 连接器（MCP，Streamable HTTP，无状态 JSON 应答）。只读：查询实时采集、坡面监测、停发设备。
// 在 Claude 的“连接器”里添加自定义连接器，地址填 https://everest-facets.yizebaba.workers.dev/mcp 。
// 只监测、不预测；数据都来自公开源。

const PROTO = ["2025-06-18", "2025-03-26", "2024-11-05"];
const BJ = t => t ? new Date(t).toLocaleString("zh-CN", { timeZone: "Asia/Shanghai", hour12: false, month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" }) : "—";
const NAMES = { evn: "IO.EVN 地震台", bipad: "尼泊尔水位站（BIPAD）", emsc: "EMSC 地震目录", gibs: "卫星云图（NASA GIBS / EUMETView）", ioda: "IODA 网络连通（萨加玛塔区）",
  usgs: "USGS 地震目录", alerts: "BIPAD 灾害警报", nsc: "尼泊尔国家地震中心", gdacs: "GDACS 灾害警报", doris: "DORIS 信标 EVEC", adsb: "ADS-B 空中交通" };

const TOOLS = [
  { name: "everest_overview", title: "珠峰监测总览",
    description: "珠峰（Everest）及周边监测的当前总览：各实时数据源是否正常、哪些台站停发、坡面雷达监测进度、需要注意的事项。只监测，不预测。",
    inputSchema: { type: "object", properties: {}, additionalProperties: false } },
  { name: "everest_water_levels", title: "冰湖与河流水位",
    description: "尼泊尔水文气象局遥测水位站（Imja、Tsho Rolpa 冰湖出口，Dudh Koshi、Arun、Bhote Koshi 等河流）的最新水位、警戒/危险水位和是否在报。可按站名关键词过滤。",
    inputSchema: { type: "object", properties: { station: { type: "string", description: "站名关键词，如 Imja、Arun、Kodari；不填返回全部" } }, additionalProperties: false } },
  { name: "everest_quakes", title: "地震与崩塌事件",
    description: "珠峰范围内近期地震和大型崩塌：USGS（含“landslide”非构造事件）、EMSC（330 km 内近 30 天）、尼泊尔国家地震中心。",
    inputSchema: { type: "object", properties: { limit: { type: "integer", minimum: 1, maximum: 30, description: "每个目录最多返回几条，默认 8" } }, additionalProperties: false } },
  { name: "everest_offline", title: "停发设备",
    description: "实时监测中没有新数据的设备：水位站（超过 6 小时无数据）、IO.EVN 地震台（20 分钟无数据，附最后数据时间）、DORIS 信标（12 小时未被跟踪）。停发不等于环境正常。",
    inputSchema: { type: "object", properties: {}, additionalProperties: false } },
  { name: "everest_facets", title: "坡面雷达监测",
    description: "珠峰周边 376 块陡冰坡面的 Sentinel-1 雷达后向散射异常监测（OCHA 方法，实时版）：基线进度，或分级结果（critical / elevated / watch）及最异常的坡面。",
    inputSchema: { type: "object", properties: { top: { type: "integer", minimum: 1, maximum: 50, description: "返回最异常的前几块坡面，默认 10" } }, additionalProperties: false } },
  { name: "everest_source", title: "单个数据源原始数据",
    description: "取某个实时数据源的最新原始结果（JSON）。可选：evn、bipad、emsc、gibs、ioda、usgs、alerts、nsc、gdacs、doris、adsb。",
    inputSchema: { type: "object", properties: { key: { type: "string", enum: Object.keys(NAMES) } }, required: ["key"], additionalProperties: false } },
  { name: "everest_snapshot", title: "完整实时快照",
    description: "一次取回全部实时采集结果（11 个数据源的最新 JSON）和坡面监测进度，供网页或程序整体刷新使用。",
    inputSchema: { type: "object", properties: {}, additionalProperties: false } },
  { name: "everest_alerts", title: "灾害警报",
    description: "尼泊尔 BIPAD 灾害警报（洪水、强降雨、森林火灾、道路中断，全国范围）和 GDACS 全球灾害警报中涉及尼泊尔的事件。只转述官方/公开警报，本平台不发布预警。",
    inputSchema: { type: "object", properties: { days: { type: "integer", minimum: 1, maximum: 30, description: "最近几天，默认 7" }, kind: { type: "string", enum: ["all", "flood", "rain", "fire", "road"], description: "类型，默认 all" } }, additionalProperties: false } },
  { name: "everest_connectivity", title: "通信连通",
    description: "萨加玛塔区（珠峰所在地区）互联网连通：IODA 的 BGP 可达网段数和主动探测（ping）数，最近 24 小时最低值和是否有中断。用来判断现场设备停发是不是因为当地断网。",
    inputSchema: { type: "object", properties: {}, additionalProperties: false } },
  { name: "everest_satellite_tracking", title: "DORIS 信标卫星跟踪",
    description: "珠峰地区 DORIS 信标 EVEC 被测高卫星（Jason-3、Sentinel-3/6、HY-2、CryoSat-2、SWOT、SARAL）跟踪的记录：最近一次过境、24 小时内过境次数。信标在被跟踪说明设备在发射。",
    inputSchema: { type: "object", properties: {}, additionalProperties: false } },
  { name: "everest_air_traffic", title: "空中交通（ADS-B）",
    description: "卢卡拉（Lukla）机场周边的 ADS-B 飞机数和最近几次采集记录。0 架可能是附近没有接收站，不等于没有飞机。",
    inputSchema: { type: "object", properties: {}, additionalProperties: false } },
  { name: "everest_imagery", title: "最新卫星云图",
    description: "珠峰范围最新的葵花（Himawari）可见光和红外云图链接（NASA GIBS）及成像时间。只是图像，不做天气预报。",
    inputSchema: { type: "object", properties: {}, additionalProperties: false } },
  { name: "everest_station_history", title: "单站水位序列",
    description: "某个水位站最近的水位时间序列（约 10 分钟一个点），附警戒/危险水位、最高最低值和变化量。station 填站名关键词或站号。",
    inputSchema: { type: "object", properties: { station: { type: "string", description: "站名关键词或站号，如 Imja、Tsho Rolpa、2874" }, hours: { type: "integer", minimum: 1, maximum: 72, description: "最近几小时，默认 24" } }, required: ["station"], additionalProperties: false } },
  { name: "everest_events", title: "事件与证据包",
    description: "自动发现的喜马拉雅上游突发事件（BIPAD 洪水警报、USGS 崩塌、GDACS 橙/红级、水位越线、两家以上媒体报道的雪崩/冰湖溃决/泥石流/滑坡新闻线索），以及每个事件的证据包：地震台（含民间地震仪）、地震目录与震动图、附近水位站、网络连通、卫星影像与洪水范围、新闻、人道报告、存证状态，按时间排在一条线上。只陈述公开来源记录，不判断成因。",
    inputSchema: { type: "object", properties: { days: { type: "integer", minimum: 1, maximum: 60, description: "最近几天，默认 30" }, id: { type: "string", description: "事件编号；填了就返回这个事件的完整证据时间线" }, full: { type: "boolean", description: "true 时返回所有事件的完整证据包（总览页用）" } }, additionalProperties: false } },
  { name: "everest_daily_brief", title: "监测日报",
    description: "一次生成珠峰监测日报：数据源状态、停发设备、近 N 小时地震与崩塌、灾害警报、水位越线站、通信连通、DORIS 跟踪、坡面进度。只监测、不预测。",
    inputSchema: { type: "object", properties: { hours: { type: "integer", minimum: 1, maximum: 72, description: "统计最近几小时，默认 24" } }, additionalProperties: false } },
];
for (const t of TOOLS) t.annotations = { readOnlyHint: true, openWorldHint: true };

// 停发判定，与 tools/monitor_sync.py 一致
export function offlineItems(rt) {
  const now = Date.parse(rt.updated || new Date().toISOString()), S = rt.sources || {}, out = [];
  for (const [sid, st] of Object.entries(((S.bipad || {}).v || {}).st || {})) {
    const m = st.meta || {}, last = m.last_on ? Date.parse(m.last_on) : null;
    if (!last || now - last > 6 * 3600e3) out.push({ key: "bipad:" + sid, name: m.name || m.title || sid, last: last ? new Date(last).toISOString() : null, note: "超过 6 小时没有新数据" + (m.status && m.status !== "BELOW WARNING LEVEL" ? "；门户状态 " + m.status : "") });
  }
  const e = (S.evn || {}).v || {};
  if (S.evn && !(e.completeness > 0)) out.push({ key: "evn", name: "IO.EVN 地震台（Pyramid）", last: e.last_seen || null, note: e.note || "最近 20 分钟没有数据" });
  const lp = ((S.doris || {}).v || {}).last_pass;
  if (S.doris && (!lp || now - Date.parse(lp.last) > 12 * 3600e3)) out.push({ key: "doris", name: "DORIS 信标 EVEC", last: lp ? lp.last : null, note: "12 小时内没有被卫星跟踪到" });
  return out;
}

async function call(name, args, h) {
  const rt = await h.rt();
  if (!rt) return { text: "实时采集还没有数据。", data: null };
  const S = rt.sources || {}, v = k => (S[k] || {}).v || {};
  if (name === "everest_overview") {
    const fs = await h.status(), off = offlineItems(rt);
    const src = Object.keys(NAMES).filter(k => S[k]).map(k => ({ key: k, name: NAMES[k], ok: !!S[k].ok, at: S[k].at, err: S[k].err || null }));
    const sc = fs.scenes || {};
    const lines = [`EVEREST 珠峰监测总览（实时采集汇总于 ${BJ(rt.updated)} 北京时间）`,
      `数据源：${src.filter(s => s.ok).length}/${src.length} 个取数正常` + (src.some(s => !s.ok) ? "；失败：" + src.filter(s => !s.ok).map(s => s.name).join("、") : ""),
      `停发设备 ${off.length} 台：` + (off.map(o => `${o.name}（最后数据 ${BJ(o.last)}）`).join("；") || "无"),
      `坡面雷达监测：` + (fs.live_at ? "已出分级（用 everest_facets 查看）" : `建立历史基线中，${sc.d || 0}/${sc.n || 0} 景`),
      `ADS-B：` + (S.adsb && S.adsb.ok ? `${v("adsb").count} 架（${v("adsb").source}）` : "不可用"),
      "只监测、不预测；停报不等于正常。"];
    return { text: lines.join("\n"), data: { updated: rt.updated, sources: src, offline: off, facets: { scenes: sc, live_at: fs.live_at } } };
  }
  if (name === "everest_water_levels") {
    const q = String(args.station || "").toLowerCase(), now = Date.parse(rt.updated);
    const st = Object.entries(v("bipad").st || {}).map(([id, s]) => { const m = s.meta || {}, o = s.obs || [], last = o.length ? o[o.length - 1] : null;
      return { id, name: m.name, title: m.title, level_m: last ? last[1] : null, at: m.last_on, warning_m: m.warning ?? null, danger_m: m.danger ?? null, status: m.status, reporting: !!(m.last_on && now - Date.parse(m.last_on) <= 6 * 3600e3), basin: m.basin };
    }).filter(s => !q || (s.name + " " + s.title).toLowerCase().includes(q));
    return { text: st.map(s => `${s.name}：${s.level_m ?? "—"} m（警戒 ${s.warning_m ?? "—"}，危险 ${s.danger_m ?? "—"}）· ${s.reporting ? "在报" : "停报"} · ${BJ(s.at)}`).join("\n") || "没有匹配的站", data: { updated: rt.updated, stations: st } };
  }
  if (name === "everest_quakes") {
    const n = Math.min(30, Math.max(1, args.limit || 8));
    const u = (v("usgs").events || []).slice(0, n), e = (v("emsc").events || []).slice(0, n), p = (v("nsc").events || []).slice(0, n);
    const f = (t, a) => t + "\n" + (a.length ? a.join("\n") : "  （无）");
    return { text: [f("USGS：", u.map(x => `  ${BJ(x.t)} M${x.mag} ${x.type === "landslide" ? "崩塌/滑坡" : x.type} · ${x.place}`)),
      f("EMSC（330 km 内近 30 天）：", e.map(x => `  ${BJ(x.t)} ${x.mt} ${x.mag} · ${x.region}`)),
      f("尼泊尔国家地震中心：", p.map(x => `  ${BJ(x.t)} ${x.mt} ${x.mag} · ${x.place}`))].join("\n"), data: { usgs: u, emsc: e, nsc: p } };
  }
  if (name === "everest_offline") {
    const off = offlineItems(rt);
    return { text: off.length ? off.map(o => `${o.name}：最后数据 ${BJ(o.last)}；${o.note}`).join("\n") + "\n停发不等于环境正常；外部设备不归本平台维修。" : "目前没有停发的设备。", data: { updated: rt.updated, offline: off } };
  }
  if (name === "everest_facets") {
    const live = await h.live(), fs = await h.status(), top = Math.min(50, Math.max(1, args.top || 10));
    if (!live) { const sc = fs.scenes || {}; return { text: `坡面基线还在建立：${sc.d || 0}/${sc.n || 0} 景已算，${fs.dates_scored}/${fs.dates_total} 个日期已打分。基线完成后才有分级。`, data: { building: true, status: fs } }; }
    const F = (live.facets || []).slice().sort((a, b) => (a.pct ?? 999) - (b.pct ?? 999));
    const cnt = {}; F.forEach(f => cnt[f.tier] = (cnt[f.tier] || 0) + 1);
    return { text: `坡面分级（最新影像 ${BJ(live.last_scene)}）：` + Object.entries(cnt).map(([k, n]) => `${k} ${n}`).join("，") + "\n最异常的坡面：\n" + F.slice(0, top).map(f => `  ${f.id} · ${f.tier}` + (f.pct != null ? ` · 历史分位 ${f.pct}%` : "")).join("\n"), data: { counts: cnt, top: F.slice(0, top), last_scene: live.last_scene } };
  }
  if (name === "everest_snapshot") {
    const fs = await h.status();
    return { text: `实时快照：汇总于 ${BJ(rt.updated)}，${Object.keys(S).length} 个数据源；坡面 ${(fs.scenes || {}).d || 0}/${(fs.scenes || {}).n || 0} 景。`, data: { rt, status: fs } };
  }
  if (name === "everest_source") {
    const k = args.key; if (!S[k]) return { text: "没有这个数据源：" + k, data: null, err: true };
    return { text: JSON.stringify(S[k]).slice(0, 20000), data: S[k] };
  }
  const now = Date.parse(rt.updated || new Date().toISOString());
  const HZ = { 11: "flood", 14: "rain", 12: "fire" }, HZN = { flood: "洪水", rain: "强降雨", fire: "森林火灾", road: "道路中断" };
  const kindOf = a => a.source === "dor" ? "road" : (HZ[a.hazard] || "other");
  const alertsIn = (hrs, kind) => (v("alerts").alerts || []).filter(a => now - Date.parse(a.started) <= hrs * 3600e3 && (!kind || kind === "all" || kindOf(a) === kind));
  const sers = s => { const o = []; (s.v || []).forEach((x, i) => { if (x != null) o.push([s.from + i * s.step, x]) }); return o };
  const ioda = () => { const I = v("ioda"), b = sers(I.bgp || {}), p = sers(I.ping || {}), cut = now / 1000 - 86400;
    const b24 = b.filter(x => x[0] >= cut).map(x => x[1]), p24 = p.filter(x => x[0] >= cut).map(x => x[1]), mx = Math.max(...b.map(x => x[1]), 0);
    const bmin = b24.length ? Math.min(...b24) : null, pmin = p24.length ? Math.min(...p24) : null;
    return { region: I.region, bgp_last: I.bgp_last, ping_last: I.ping_last, bgp_min_24h: bmin, ping_min_24h: pmin, bgp_max: mx, outage: bmin != null && mx > 0 && bmin < mx * 0.5, until: I.until } };
  const findSt = q => { q = String(q || "").toLowerCase(); return Object.entries(v("bipad").st || {}).filter(([id, s]) => { const m = s.meta || {}; return id === q || ((m.name || "") + " " + (m.title || "")).toLowerCase().includes(q) }) };
  if (name === "everest_alerts") {
    const days = Math.min(30, Math.max(1, args.days || 7)), A = alertsIn(days * 24, args.kind), G = (v("gdacs").events || []);
    return { text: `BIPAD 灾害警报（尼泊尔全国，最近 ${days} 天，${A.length} 条）：\n` + (A.map(a => `  ${BJ(a.started)} ${HZN[kindOf(a)] || "其他"} · ${a.title}` + (a.expire ? "（已结束）" : "（未标结束）")).join("\n") || "  （无）") +
      `\nGDACS（涉及尼泊尔）：\n` + (G.map(g => `  ${g.level} ${g.name} · ${g.from.slice(0, 10)} 至 ${String(g.to || "").slice(0, 10)}`).join("\n") || "  （无）") + "\n本平台只转述公开警报，不发布预警。", data: { bipad: A, gdacs: G } };
  }
  if (name === "everest_connectivity") {
    const c = ioda();
    return { text: `${c.region} 互联网连通（IODA）：BGP 可达网段 ${c.bgp_last ?? "—"}（24 小时最低 ${c.bgp_min_24h ?? "—"}），主动探测 ${c.ping_last ?? "—"}（最低 ${c.ping_min_24h ?? "—"}）。` + (c.outage ? "24 小时内出现过明显下降，现场设备停发可能与断网有关。" : "24 小时内没有明显中断。"), data: c };
  }
  if (name === "everest_satellite_tracking") {
    const D = v("doris"), lp = D.last_pass, SN = { h2c: "HY-2C", h2d: "HY-2D", s3a: "Sentinel-3A", s3b: "Sentinel-3B", s6a: "Sentinel-6A", ja3: "Jason-3", cs2: "CryoSat-2", swo: "SWOT", srl: "SARAL" };
    return { text: `DORIS 信标 EVEC：最近一次被跟踪 ${lp ? BJ(lp.last) + "（" + (SN[lp.sat] || lp.sat) + "，" + lp.n + " 个测量）" : "—"}；24 小时内过境 ${D.passes_24h ?? "—"} 次。\n最近过境：\n` + (D.passes || []).slice(-8).reverse().map(p => `  ${BJ(p.first)} ${SN[p.sat] || p.sat} · ${p.n} 个测量`).join("\n"), data: { last_pass: lp, passes_24h: D.passes_24h, passes: D.passes } };
  }
  if (name === "everest_air_traffic") {
    const A = v("adsb");
    return { text: `卢卡拉周边 ADS-B：${A.count ?? "—"} 架（${A.source || "—"}，采集于 ${BJ(A.fetched)}）。` + (A.count ? "\n" + (A.now || []).map(a => "  " + JSON.stringify(a)).join("\n") : "\n0 架可能是附近没有接收站，不等于没有飞机。") + "\n最近记录：" + (A.hist || []).slice(-6).map(h => BJ(h[0]) + " " + h[1] + " 架").join("；"), data: A };
  }
  if (name === "everest_imagery") {
    const I = v("gibs");
    return { text: `珠峰范围卫星云图（NASA GIBS，葵花卫星）：\n可见光（${BJ(I.vis_latest)}）：${(I.img || {}).vis}\n红外（${BJ(I.ir_latest)}）：${(I.img || {}).ir}\n只是图像，不做天气预报。`, data: I };
  }
  if (name === "everest_station_history") {
    const hrs = Math.min(72, Math.max(1, args.hours || 24)), L = findSt(args.station);
    if (!L.length) return { text: "没有匹配的站：" + args.station + "。可用 everest_water_levels 看全部站名。", data: null, err: true };
    const out = L.slice(0, 3).map(([id, s]) => { const m = s.meta || {}, o = (s.obs || []).filter(x => now - Date.parse(x[0]) <= hrs * 3600e3), ls = o.map(x => x[1]);
      return { id, name: m.name, warning_m: m.warning ?? null, danger_m: m.danger ?? null, status: m.status, last_on: m.last_on, n: o.length, min: ls.length ? Math.min(...ls) : null, max: ls.length ? Math.max(...ls) : null, change: ls.length > 1 ? +(ls[ls.length - 1] - ls[0]).toFixed(3) : null, obs: o } });
    return { text: out.map(x => `${x.name}（站号 ${x.id}）最近 ${hrs} 小时 ${x.n} 个点` + (x.n ? `：最低 ${x.min} m，最高 ${x.max} m，变化 ${x.change ?? 0} m` : `：没有数据（最后数据 ${BJ(x.last_on)}）`) + `；警戒 ${x.warning_m ?? "—"}，危险 ${x.danger_m ?? "—"}`).join("\n"), data: { stations: out } };
  }
  if (name === "everest_events") {
    const days = Math.min(60, Math.max(1, args.days || 30)), E = Object.values((h.events ? await h.events() : {}) || {}).filter(e => now - Date.parse(e.t) <= days * 864e5).sort((a, b) => b.t.localeCompare(a.t));
    let idx = {}; try { const r = await fetch(`https://raw.githubusercontent.com/Yizebaba/EVEREST-/events/index.json`, { cf: { cacheTtl: 120 } }); if (r.ok) idx = (await r.json()).events || {}; } catch (e) {}
    if (args.id) {
      const e = E.find(x => x.id === args.id) || Object.values((await h.events()) || {}).find(x => x.id === args.id); if (!e) return { text: "没有这个事件：" + args.id, data: null, err: true };
      let pack = null; try { const r = await fetch(`https://raw.githubusercontent.com/Yizebaba/EVEREST-/events/events/${e.id}.json`); if (r.ok) pack = await r.json(); } catch (x) {}
      const tl = (pack && pack.timeline) || e.src;
      return { text: `${e.title}（${e.place || ""}）\n事件时间（最早信号）：${BJ(e.t)} 北京时间\n` + (pack ? `证据包生成于 ${BJ(pack.built)}\n` : "证据包还没生成\n") + tl.map(x => `  ${BJ(x.t)} [${x.src}] ${x.text}` + (x.status ? `（${x.status}）` : "")).join("\n") + "\n只陈述公开来源记录，不判断成因。", data: { event: e, pack } };
    }
    if (args.full) {   // 总览页用：完整证据包（不含图），页面有更新就拉
      const L = [];
      for (const e of E.slice(0, 10)) {
        let p = null; try { const r = await fetch(`https://raw.githubusercontent.com/Yizebaba/EVEREST-/events/events/${e.id}.json`, { cf: { cacheTtl: 60 } }); if (r.ok) p = await r.json(); } catch (x) {}
        if (!p) continue; const m = idx[e.id] || {};
        L.push({ id: p.id, hips: p.hips || e.hips || [], title: p.title, title_en: p.title_en, kind: p.kind, place: p.place, lat: p.lat, lon: p.lon, t: p.t, built: p.built, note: p.note, note_en: p.note_en, first_seen: m.first_seen || e.first_seen,
          timeline: (p.timeline || []).slice(0, 80), evn: p.evn ? { distance_km: p.evn.distance_km, coverage_pct: p.evn.coverage_pct, peaks: p.evn.peaks, error: p.evn.error } : null,
          kkn: p.kkn || null, gfm: p.gfm || null, sentinel: p.sentinel || null, gauges: p.gauges || null, ioda: p.ioda || null, manual: p.manual || null, news: (p.news || []).slice(0, 10), ots: m.ots || [], png: p.png || null });
      }
      return { text: `${L.length} 个事件的完整证据包`, data: { updated: new Date().toISOString(), events: L } };
    }
    return { text: E.length ? E.map(e => `${BJ(e.t)} ${e.kind} · ${e.title} · ${e.src.length} 条信号` + (idx[e.id] ? ` · 证据包 ${idx[e.id].n} 条` : " · 证据包待生成") + `（编号 ${e.id}）`).join("\n") : `最近 ${days} 天没有自动发现的事件。`, data: { events: E, packs: idx } };
  }
  if (name === "everest_daily_brief") {
    const hrs = Math.min(72, Math.max(1, args.hours || 24)), fs = await h.status(), off = offlineItems(rt), sc = fs.scenes || {};
    const src = Object.keys(NAMES).filter(k => S[k]), bad = src.filter(k => !S[k].ok);
    const inH = t => t && now - Date.parse(t) <= hrs * 3600e3;
    const qs = [...(v("usgs").events || []).filter(x => inH(x.t)).map(x => `USGS ${BJ(x.t)} M${x.mag} ${x.type === "landslide" ? "崩塌/滑坡" : ""} ${x.place}`), ...(v("emsc").events || []).filter(x => inH(x.t)).map(x => `EMSC ${BJ(x.t)} ${x.mt} ${x.mag} ${x.region}`), ...(v("nsc").events || []).filter(x => inH(x.t)).map(x => `NSC ${BJ(x.t)} ${x.mt} ${x.mag} ${x.place}`)];
    const A = alertsIn(hrs), over = Object.entries(v("bipad").st || {}).map(([id, s]) => s.meta || {}).filter(m => m.status && m.status !== "BELOW WARNING LEVEL" && m.last_on && now - Date.parse(m.last_on) <= 6 * 3600e3);
    const c = ioda(), lp = v("doris").last_pass;
    const L = [`EVEREST 监测日报（最近 ${hrs} 小时，截至 ${BJ(rt.updated)} 北京时间）`,
      `一、数据源：${src.length - bad.length}/${src.length} 正常` + (bad.length ? "；失败：" + bad.map(k => NAMES[k]).join("、") : ""),
      `二、停发设备 ${off.length} 台：` + (off.map(o => `${o.name}（最后数据 ${BJ(o.last)}）`).join("；") || "无"),
      `三、地震与崩塌 ${qs.length} 条：` + (qs.length ? "\n  " + qs.join("\n  ") : "无"),
      `四、灾害警报（尼泊尔全国）${A.length} 条：` + (A.length ? "\n  " + A.map(a => `${BJ(a.started)} ${a.title}`).join("\n  ") : "无"),
      `五、在报水位站越过警戒线：` + (over.map(m => `${m.name}（${m.status}）`).join("；") || "无"),
      `六、通信：${c.region} BGP ${c.bgp_last ?? "—"}（24h 最低 ${c.bgp_min_24h ?? "—"}）` + (c.outage ? "，出现过明显下降" : "，无明显中断"),
      `七、DORIS 信标：最近被跟踪 ${lp ? BJ(lp.last) : "—"}，24 小时 ${v("doris").passes_24h ?? "—"} 次`,
      `八、坡面雷达：` + (fs.live_at ? "已出分级（everest_facets）" : `基线 ${sc.d || 0}/${sc.n || 0} 景`),
      "只监测、不预测；停报不等于正常；外部设备不归本平台维修。"];
    return { text: L.join("\n"), data: { updated: rt.updated, hours: hrs, offline: off, quakes: qs, alerts: A, over_warning: over, connectivity: c, doris_last: lp, facets: sc } };
  }
  return { text: "未知工具：" + name, data: null, err: true };
}

export async function handleMcp(req, env, h) {
  const hdr = { "content-type": "application/json", "access-control-allow-origin": "*", "access-control-allow-headers": "content-type, mcp-protocol-version, mcp-session-id", "access-control-allow-methods": "POST, OPTIONS" };
  if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: hdr });
  if (req.method !== "POST") return new Response(JSON.stringify({ error: "MCP 连接器只接受 POST；在 Claude 的连接器里添加这个地址即可" }), { status: 405, headers: { ...hdr, allow: "POST" } });
  let msg; try { msg = await req.json(); } catch { return new Response(JSON.stringify({ jsonrpc: "2.0", id: null, error: { code: -32700, message: "Parse error" } }), { status: 400, headers: hdr }); }
  const one = async m => {
    if (!m || m.jsonrpc !== "2.0" || typeof m.method !== "string") return { jsonrpc: "2.0", id: m && m.id || null, error: { code: -32600, message: "Invalid Request" } };
    if (m.id === undefined) return null;                      // 通知（如 notifications/initialized）不回
    const ok = r => ({ jsonrpc: "2.0", id: m.id, result: r });
    if (m.method === "initialize") {
      const want = (m.params || {}).protocolVersion;
      return ok({ protocolVersion: PROTO.includes(want) ? want : PROTO[0], capabilities: { tools: { listChanged: false } },
        serverInfo: { name: "everest", title: "EVEREST 公开地球观测数据的真实度审计和事件证据平台", version: "1.1.0" },
        instructions: "EVEREST：公开地球观测数据的真实度审计和事件证据平台。只监测、不预测、不做天气。先用 everest_overview 看总览（各来源是否在线、停发设备），需要时查水位、地震、警报、通信、DORIS、坡面，或用 everest_daily_brief 出日报。时间默认北京时间；每个数字注明来源。" });
    }
    if (m.method === "ping") return ok({});
    if (m.method === "tools/list") return ok({ tools: TOOLS });
    if (m.method === "tools/call") {
      const p = m.params || {}, t = TOOLS.find(x => x.name === p.name);
      if (!t) return { jsonrpc: "2.0", id: m.id, error: { code: -32602, message: "Unknown tool: " + p.name } };
      try { const r = await call(p.name, p.arguments || {}, h); return ok({ content: [{ type: "text", text: r.text }], ...(r.data ? { structuredContent: { result: r.data } } : {}), isError: !!r.err }); }
      catch (e) { return ok({ content: [{ type: "text", text: "出错：" + String(e && e.message || e) }], isError: true }); }
    }
    if (m.method === "resources/list") return ok({ resources: [] });
    if (m.method === "prompts/list") return ok({ prompts: [] });
    return { jsonrpc: "2.0", id: m.id, error: { code: -32601, message: "Method not found: " + m.method } };
  };
  if (Array.isArray(msg)) { const r = (await Promise.all(msg.map(one))).filter(Boolean); return r.length ? new Response(JSON.stringify(r), { headers: hdr }) : new Response(null, { status: 202, headers: hdr }); }
  const r = await one(msg);
  return r ? new Response(JSON.stringify(r), { headers: hdr }) : new Response(null, { status: 202, headers: hdr });
}
