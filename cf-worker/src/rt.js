// 珠峰实时源采集（在 everest-facets Worker 里运行，每 5 分钟一轮，按各源自己的节奏取数）。
// 只监测：记录“最新是什么、什么时候”，不判断、不预测。
import { connect } from "cloudflare:sockets";

const LAT = 27.988, LON = 86.925;
export const IMG = {
  himawari_vis: "https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi?SERVICE=WMS&REQUEST=GetMap&VERSION=1.3.0&LAYERS=Himawari_AHI_Band3_Red_Visible_1km&CRS=EPSG:4326&BBOX=27.3,86.2,28.7,87.7&WIDTH=450&HEIGHT=420&FORMAT=image/png&STYLES=",
  himawari_ir: "https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi?SERVICE=WMS&REQUEST=GetMap&VERSION=1.3.0&LAYERS=Himawari_AHI_Band13_Clean_Infrared&CRS=EPSG:4326&BBOX=27.3,86.2,28.7,87.7&WIDTH=450&HEIGHT=420&FORMAT=image/png&STYLES=",
  meteosat_snow: "https://view.eumetsat.int/geoserver/ows?service=WMS&version=1.3.0&request=GetMap&layers=msg_iodc:rgb_snow&styles=&crs=EPSG:4326&BBOX=27.3,86.2,28.7,87.7&WIDTH=450&HEIGHT=420&format=image/png",
  meteosat_natural: "https://view.eumetsat.int/geoserver/ows?service=WMS&version=1.3.0&request=GetMap&layers=msg_iodc:rgb_naturalenhncd&styles=&crs=EPSG:4326&BBOX=27.3,86.2,28.7,87.7&WIDTH=450&HEIGHT=420&format=image/png",
};
// 各源节奏（分钟）
const EVERY = { evn: 5, bipad: 10, emsc: 10, gibs: 10, ioda: 10, usgs: 15, alerts: 15, nsc: 30, gdacs: 30, doris: 30, adsb: 30 };
const MAX_PER_ROUND = 5;   // 每轮最多跑 5 个源（按最久没更新的先跑），控制单次计算量
// 南坡关键水文站（BIPAD stationSeriesId）
export const SERIES = { 5385: "Imja 冰湖出口", 5378: "Imja 湖下游（疑似故障）", 12378: "Imja 河 Dingboche", 5287: "Imja 河 Pangboche",
  1867: "Tsho Rolpa 冰湖出口", 1877: "Rolwaling 河 Bedding", 1500: "杜德科西 Rabuwabazar", 26631: "杜德科西 Jayaramghat",
  23263: "阿伦河 Kimathanka", 2874: "阿伦河 Uwa Gau", 21089: "Barun 河 Syaksila", 1481: "阿伦河 Turkeghat",
  22609: "博特科西 Kodari", 1640: "博特科西 Bahrabise", 1508: "萨普塔科西 Chatara" };
const UA = { "user-agent": "everest-facets-worker (github.com/Yizebaba/everest-insar-pipeline)" };
const iso = d => new Date(d).toISOString();

async function j(url, opt = {}) { const r = await fetch(url, { ...opt, headers: { ...UA, ...(opt.headers || {}) } }); if (!r.ok) throw new Error(`${r.status} ${url.slice(0, 60)}`); return r.json(); }
async function t(url) { const r = await fetch(url, { headers: UA }); if (!r.ok) throw new Error(`${r.status} ${url.slice(0, 60)}`); return r.text(); }

// ---- 各源 ----
// 尼泊尔减灾局 BIPAD：河流 / 冰湖出口水位（转发尼泊尔水文气象局遥测）
async function bipad(prev) {
  const st = prev || { st: {} }; let seen = 0;
  for (let off = 0; off < 700 && seen < Object.keys(SERIES).length; off += 100) {
    const rows = (await j(`https://bipadportal.gov.np/api/v1/river-stations/?format=json&limit=100&offset=${off}`)).results || [];
    if (!rows.length) break;
    for (const r of rows) {
      const nm = SERIES[r.stationSeriesId]; if (!nm) continue; seen++;
      const k = String(r.stationSeriesId), pt = (r.point || {}).coordinates || [null, null];
      const d = st.st[k] || { obs: [] };
      d.meta = { name: nm, title: r.title, lon: pt[0], lat: pt[1], warning: r.warningLevel, danger: r.dangerLevel, status: r.status, basin: r.basin, last_on: r.waterLevelOn };
      if (r.waterLevelOn && r.waterLevel != null) { const tu = iso(r.waterLevelOn); if (!d.obs.length || d.obs[d.obs.length - 1][0] !== tu) d.obs.push([tu, Math.round(r.waterLevel * 1000) / 1000]); }
      d.obs = d.obs.filter(o => Date.now() - Date.parse(o[0]) < 3 * 864e5).slice(-300);
      st.st[k] = d;
    }
  }
  if (!seen) throw new Error("BIPAD 没返回目标站");
  st.seen = seen; return st;
}
async function alerts() {
  const rows = (await j("https://bipadportal.gov.np/api/v1/alert/?format=json&ordering=-started_on&limit=30")).results || [];
  return { alerts: rows.map(r => ({ title: r.title, started: r.startedOn, expire: r.expireOn, hazard: r.hazard, source: r.source })) };
}
async function usgs() {
  const start = new Date(Date.now() - 60 * 864e5).toISOString().slice(0, 10);
  const x = await j(`https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&orderby=time&minlatitude=26.3&maxlatitude=29.8&minlongitude=84.5&maxlongitude=89.0&starttime=${start}`);
  return { events: (x.features || []).map(f => ({ id: f.id, t: iso(f.properties.time), mag: f.properties.mag, type: f.properties.type, place: f.properties.place, url: f.properties.url, lon: f.geometry.coordinates[0], lat: f.geometry.coordinates[1] })) };
}
// 意大利 OGS 地震台 IO.EVN：从 GEOFON 取最近 20 分钟 BHZ 的 miniSEED，只读记录头（不解压波形），得到最新样点时刻和数据完整度
async function evn() {
  const end = new Date(), start = new Date(end - 20 * 60e3), f = d => d.toISOString().slice(0, 19);
  const r = await fetch(`https://geofon.gfz.de/fdsnws/dataselect/1/query?net=IO&sta=EVN&cha=BHZ&starttime=${f(start)}&endtime=${f(end)}`, { headers: UA });
  if (r.status === 204) return { last_sample: null, lag_s: null, completeness: 0, note: "最近 20 分钟没有数据" };
  if (!r.ok) throw new Error(`GEOFON ${r.status}`);
  const b = new DataView(await r.arrayBuffer());
  let off = 0, last = 0, n = 0, rate = 0, recs = 0;
  while (off + 48 <= b.byteLength) {
    const yr = b.getUint16(off + 20), doy = b.getUint16(off + 22), hh = b.getUint8(off + 24), mi = b.getUint8(off + 25), ss = b.getUint8(off + 26), fr = b.getUint16(off + 28);
    const ns = b.getUint16(off + 30), fac = b.getInt16(off + 32), mul = b.getInt16(off + 34);
    const sr = fac > 0 ? (mul > 0 ? fac * mul : -fac / mul) : (mul > 0 ? -mul / fac : 1 / (fac * mul));
    const t0 = Date.UTC(yr, 0, doy, hh, mi, ss) + fr / 10;
    if (sr > 0 && ns > 0) { last = Math.max(last, t0 + (ns - 1) / sr * 1000); n += ns; rate = sr; }
    // 记录长度在 blockette 1000 里（2^exp）
    let len = 512, bo = b.getUint16(off + 46);
    for (let k = 0; k < 4 && bo && bo + 8 <= 4096 && off + bo + 8 <= b.byteLength; k++) {
      if (b.getUint16(off + bo) === 1000) { len = 2 ** b.getUint8(off + bo + 6); break; }
      bo = b.getUint16(off + bo + 2);
    }
    off += len; recs++;
  }
  if (!recs) throw new Error("miniSEED 解析不到记录");
  return { last_sample: iso(last), lag_s: Math.round((end - last) / 1000), completeness: rate ? Math.round(n / (rate * 1200) * 100) : null, rate, records: recs };
}

async function gibs() {
  const d = new Date().toISOString().slice(0, 10);
  const last = async layer => {
    const x = await t(`https://gibs.earthdata.nasa.gov/wmts/epsg4326/best/1.0.0/${layer}/default/2km/all/${d}T00:00:00Z--${d}T23:59:59Z.xml`);
    const dom = (x.match(/<Domain>([^<]+)<\/Domain>/) || [])[1] || "";
    const ends = dom.split(",").map(s => s.split("/")[1]).filter(Boolean).sort();
    return ends.length ? ends[ends.length - 1] : null;
  };
  return { vis_latest: await last("Himawari_AHI_Band3_Red_Visible_1km"), ir_latest: await last("Himawari_AHI_Band13_Clean_Infrared"), img: { vis: IMG.himawari_vis, ir: IMG.himawari_ir } };
}
async function emsc() {
  const start = new Date(Date.now() - 30 * 864e5).toISOString().slice(0, 10);
  const x = await j(`https://www.seismicportal.eu/fdsnws/event/1/query?lat=${LAT}&lon=${LON}&maxradius=3&starttime=${start}&format=json&limit=50&orderby=time`);
  return { events: (x.features || []).map(f => ({ t: f.properties.time, mag: f.properties.mag, mt: f.properties.magtype, region: f.properties.flynn_region,
    lat: f.properties.lat, lon: f.properties.lon, depth: f.properties.depth, id: f.properties.unid })) };
}
async function nsc() {
  const h = await t("https://seismonepal.gov.np/");
  const rows = [...h.matchAll(/<tr[^>]*>([\s\S]*?)<\/tr>/g)].slice(1, 16).map(m => m[1].replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim());
  const ev = rows.map(r => {
    // 日期是尼泊尔当地日期，时间取当地时间再减 5:45 换成 UTC（UTC 可能是前一天）
    const m = r.match(/ई\.सं\.:\s*(\d{4}-\d\d-\d\d).*?स्थानीय:\s*(\d\d:\d\d:\d\d).*?UTC:\s*\d\d:\d\d:\d\d\s+([\d.]+)°\s+([\d.]+)°\s+([\d.]+)\s*(\w+)\s+(.*?)\s+Did you feel/);
    return m ? { t: iso(Date.parse(`${m[1]}T${m[2]}+05:45`)), lat: +m[3], lon: +m[4], mag: +m[5], mt: m[6], place: m[7] } : null;
  }).filter(Boolean);
  if (!ev.length) throw new Error("NSC 页面格式变了，没解析到地震");
  return { events: ev };
}
async function ioda(prev) {
  const until = Math.floor(Date.now() / 1000), from = until - 24 * 3600;
  const x = await j(`https://api.ioda.inetintel.cc.gatech.edu/v2/signals/raw/region/3027?from=${from}&until=${until}`);
  const flat = Array.isArray(x.data?.[0]) ? x.data[0] : (x.data || []);
  const pick = name => { const s = flat.find(z => z.datasource === name); if (!s) return null;
    const v = (s.values || []).map(a => (typeof a === "number" ? a : null)); return { from: s.from, step: s.step, v: v.filter((_, i) => i % 2 === 0).slice(-144) }; };
  const bgp = pick("bgp"), ping = pick("ping-slash24");
  const lastNum = s => s ? [...s.v].reverse().find(a => a != null) ?? null : null;
  return { region: "Sagarmatha (3027)", bgp_last: lastNum(bgp), ping_last: lastNum(ping), bgp, ping, until: iso(until * 1000) };
}
async function adsb(prev) {
  // 三个免费 ADS-B 源依次尝试（adsb.lol 会对共享出口 IP 限流）
  let x = null, src = null, errs = [];
  for (const [name, u] of [["adsb.lol", "https://api.adsb.lol/v2/point/27.85/86.80/40"], ["adsb.fi", "https://opendata.adsb.fi/api/v3/lat/27.85/lon/86.80/dist/40"],
                           ["airplanes.live", "https://api.airplanes.live/v2/point/27.85/86.80/40"]]) {
    try { x = await j(u); src = name; break; } catch (e) { errs.push(name + ":" + String(e.message || e).slice(0, 4)); }
  }
  let ac = null;
  if (x) ac = (x.ac || x.aircraft || []).map(a => ({ hex: a.hex, flight: (a.flight || "").trim(), type: a.t || null, alt: a.alt_baro, gs: a.gs, lat: a.lat, lon: a.lon, seen: a.seen }));
  else {
    // 第四个：OpenSky Network（匿名每天 400 点额度，小范围查询 1 点/次）
    try {
      const o = await j("https://opensky-network.org/api/states/all?lamin=27.45&lomin=86.35&lamax=28.25&lomax=87.25");
      src = "opensky";
      ac = (o.states || []).map(v => ({ hex: v[0], flight: (v[1] || "").trim(), type: null, alt: v[7] == null ? null : Math.round(v[7] * 3.281), gs: v[9] == null ? null : Math.round(v[9] * 1.944), lat: v[6], lon: v[5], seen: o.time - v[4] }));
    } catch (e) { errs.push("opensky:" + String(e.message || e).slice(0, 4)); }
  }
  if (!ac) throw new Error("ADS-B 四个源都失败 " + errs.join(" "));
  const hist = ((prev && prev.hist) || []).filter(h => Date.now() - Date.parse(h[0]) < 24 * 3600e3);
  hist.push([iso(Date.now()), ac.length]);
  return { now: ac, count: ac.length, hist: hist.slice(-300), source: src };
}
async function gdacs() {
  const from = new Date(Date.now() - 90 * 864e5).toISOString().slice(0, 10);
  const out = []; let fails = 0, lastErr = null;
  for (const c of ["Nepal", "China"]) {
    // GDACS 没有事件时可能返回 404/空，这里只在两个都失败时才报错
    const x = await j(`https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH?country=${c}&fromdate=${from}`).catch(e => { fails++; lastErr = e; return { features: [] }; });
    for (const f of x.features || []) {
      const p = f.properties, g = f.geometry && f.geometry.coordinates;
      if (c === "China" && g && (Math.abs(g[1] - LAT) > 4 || Math.abs(g[0] - LON) > 6)) continue;   // 中国只留珠峰附近
      out.push({ type: p.eventtype, name: p.name, from: p.fromdate, to: p.todate, level: p.alertlevel, url: p.url && p.url.report, lat: g && g[1], lon: g && g[0] });
    }
  }
  if (fails === 2 && !String(lastErr).includes("404")) throw lastErr;
  out.sort((a, b) => (b.from || "").localeCompare(a.from || ""));
  return { events: out.slice(0, 20) };
}

// ---- DORIS：IGN 匿名 FTP（Worker TCP sockets），每次轮换一颗卫星，找 EVEC 被跟踪的时段 ----
const SATS = ["srl", "s6a", "ja3", "s3a", "s3b", "swo", "h2c", "h2d", "cs2"];
const dec = new TextDecoder("latin1"), enc = new TextEncoder();
async function readAll(sock, max = 8e6) {
  const r = sock.readable.getReader(), parts = []; let n = 0;
  for (;;) { const { value, done } = await r.read(); if (done) break; parts.push(value); n += value.length; if (n > max) break; }
  const b = new Uint8Array(n); let o = 0; for (const p of parts) { b.set(p.subarray(0, Math.min(p.length, n - o)), o); o += p.length; if (o >= n) break; }
  return b;
}
class Ftp {
  constructor(host, port = 21) { this.host = host; this.port = port; this.buf = ""; }
  async open() { this.s = connect({ hostname: this.host, port: this.port }); this.r = this.s.readable.getReader(); this.w = this.s.writable.getWriter(); return this.reply(); }
  async reply() {
    for (;;) {
      const lines = this.buf.split("\r\n");
      for (let i = 0; i < lines.length - 1; i++) if (/^\d{3} /.test(lines[i])) { this.buf = lines.slice(i + 1).join("\r\n"); return lines[i]; }
      const { value, done } = await this.r.read(); if (done) throw new Error("FTP 连接被关闭"); this.buf += dec.decode(value);
    }
  }
  async cmd(c) { await this.w.write(enc.encode(c + "\r\n")); return this.reply(); }
  async data(c) {
    const p = await this.cmd("PASV"); const m = p.match(/(\d+),(\d+),(\d+),(\d+),(\d+),(\d+)/); if (!m) throw new Error("PASV " + p);
    // 与 Python ftplib 默认做法一致：忽略 PASV 里的 IP（服务器可能给内网地址），用控制连接的主机名
    const ds = connect({ hostname: this.host, port: (+m[5]) * 256 + (+m[6]) });
    const pre = await this.cmd(c); if (!/^1\d\d/.test(pre)) { ds.close(); throw new Error(c + " " + pre); }
    const b = await readAll(ds); await this.reply(); return b;
  }
  close() { try { this.s.close(); } catch {} }
}
async function doris(prev, env) {
  const st = prev || { sats: {}, passes: [] };
  const sat = SATS[(st.k || 0) % SATS.length];
  const f = new Ftp(env && env.DORIS_HOST || "doris.ign.fr", Number(env && env.DORIS_PORT || 21));
  let info = { sat };
  try {
    await f.open(); await f.cmd("USER anonymous"); await f.cmd("PASS everest-facets@"); await f.cmd("TYPE I");
    const names = dec.decode(await f.data(`NLST /pub/doris/data/${sat}/NRT`)).split(/\r?\n/).map(s => s.trim().split("/").pop()).filter(n => n && /rx\d{8}_\d{6}/.test(n)).sort();
    const done = new Set((st.sats[sat] && st.sats[sat].files) || []);
    const todo = names.slice(-12).filter(n => !done.has(n)).slice(-3);   // 最近约一天里没看过的，每次最多 3 个
    info.newest_file = names[names.length - 1] || null;
    const dbg = [];
    for (const n of todo) {
      const txt = dec.decode(await f.data(`RETR /pub/doris/data/${sat}/NRT/${n}`));
      done.add(n);
      const cut = txt.indexOf("END OF HEADER");
      const hs = txt.lastIndexOf("\n", txt.indexOf("EVEC")) + 1;
      const ev = txt.indexOf("EVEC") > -1 && txt.indexOf("EVEC") < cut ? txt.slice(hs, txt.indexOf("\n", hs)) : null;
      const d = { f: n.slice(5, 20), kb: Math.round(txt.length / 1024), evec_ref: !!(ev && ev.includes("STATION REFERENCE")), n: 0 };
      if (d.evec_ref) {
        const id = "\n" + ev.trim().split(/\s+/)[0] + " ";
        let p = txt.indexOf(id, cut), first = null, last = null;
        while (p > -1) {
          const e = txt.lastIndexOf("\n>", p);
          const ep = txt.slice(e + 3, e + 22);
          if (!first) first = ep; last = ep; d.n++;
          p = txt.indexOf(id, p + 4);
        }
        if (d.n) st.passes.push({ sat, first: tsOf(first), last: tsOf(last), n: d.n, file: n });
      }
      dbg.push(d);
    }
    info.dbg = dbg;
    st.sats[sat] = { checked: iso(Date.now()), newest_file: info.newest_file, files: [...done].slice(-16), dbg: info.dbg };
  } finally { f.close(); }
  st.k = (st.k || 0) + 1;
  st.passes = st.passes.filter(p => Date.now() - Date.parse(p.last) < 72 * 3600e3).sort((a, b) => a.last.localeCompare(b.last)).slice(-80);
  st.last_pass = st.passes.length ? st.passes[st.passes.length - 1] : (prev && prev.last_pass) || null;
  st.passes_24h = st.passes.filter(p => Date.now() - Date.parse(p.last) < 24 * 3600e3).length;
  return st;
}
const tsOf = s => { if (!s) return null; const p = s.trim().split(/\s+/).map(Number); return iso(Date.UTC(p[0], p[1] - 1, p[2], p[3], p[4], Math.floor(p[5] || 0))); };

const JOBS = { evn, bipad, emsc, gibs, ioda, usgs, alerts, nsc, gdacs, doris, adsb };

// 每轮：取状态，跑到点的源，存回。返回本轮日志。
export async function rtTick(env, getMeta, setMeta) {
  const st = JSON.parse((await getMeta(env, "rt")) || "{}");
  const log = { rt: [] };
  const due = Object.keys(JOBS).filter(k => { const s = st[k]; return !s || !s.at || Date.now() - Date.parse(s.at) >= (EVERY[k] - 0.5) * 60e3; })
    .sort((a, b) => (Date.parse((st[a] || {}).at || 0) - (EVERY[a] * 60e3)) - (Date.parse((st[b] || {}).at || 0) - (EVERY[b] * 60e3))).slice(0, MAX_PER_ROUND);
  for (const k of due) {
    const fn = JOBS[k], s = st[k] || {};
    const t0 = Date.now();
    try {
      const v = await Promise.race([fn(s.v, env), new Promise((_, rej) => setTimeout(() => rej(new Error("超时 40 秒")), 40e3))]);
      st[k] = { at: iso(Date.now()), ok: true, v, ms: Date.now() - t0 }; log.rt.push(k);
    } catch (e) { st[k] = { ...s, at: iso(Date.now()), ok: false, err: String(e && e.message || e).slice(0, 200), ms: Date.now() - t0 }; log.rt.push(k + "!"); }
    st.updated = iso(Date.now());
    await setMeta(env, "rt", JSON.stringify(st));   // 每个源做完就存，一个卡住不影响其他
  }
  st.updated = iso(Date.now());
  await setMeta(env, "rt", JSON.stringify(st));
  return log;
}

// 给 GitHub / 页面用的精简版（去掉内部记账）
export function rtPublic(st) {
  const o = { updated: st.updated, sources: {} };
  for (const k of Object.keys(JOBS)) {
    const s = st[k]; if (!s) continue;
    let v = s.v;
    if (k === "doris" && v) v = { last_pass: v.last_pass, passes_24h: v.passes_24h, passes: (v.passes || []).slice(-30), sats: Object.fromEntries(Object.entries(v.sats || {}).map(([a, b]) => [a, { checked: b.checked, newest_file: b.newest_file, dbg: b.dbg }])) };
    o.sources[k] = { at: s.at, ok: s.ok, err: s.err || null, v };
  }
  return o;
}
