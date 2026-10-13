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
        serverInfo: { name: "everest", title: "EVEREST 珠峰监测", version: "1.0.0" },
        instructions: "EVEREST 珠峰多源监测（只监测、不预测）。先用 everest_overview 看总览，再按需查水位、地震、停发设备、坡面。时间默认北京时间。" });
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
