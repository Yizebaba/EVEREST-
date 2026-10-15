// 总览页需要、但原来只能靠定时任务写进页面数据库的几份数据，改由连接器直接给（v78）。
// 格式与 tools/hub_sync.py 生成的 live_img / live_cam / live_lib / live_lit / live_ops 完全相同，页面用同一套代码处理。
// 来源都是仓库里已有的文件：facet-live 分支的 img/*.jpg、events 分支的 hazards/*.json；
// 运行记录和设备在线状态要用 GitHub Actions 接口，由 hazards 工作流每次扫描后写到 events 分支 hub/ops.json、hub/mt_monitor.json。

const RAW = "https://raw.githubusercontent.com/Yizebaba/EVEREST-/";
const UA = { "user-agent": "everest-facets-worker" };

async function raw(path, ref, ttl = 120) {
  const r = await fetch(RAW + ref + "/" + path, { headers: UA, cf: { cacheTtl: ttl } });
  if (!r.ok) throw new Error(path + " HTTP " + r.status);
  return r;
}
const j = async (p, ref, ttl) => (await raw(p, ref, ttl)).json();
function b64(buf) {
  const b = new Uint8Array(buf); let s = "";
  for (let i = 0; i < b.length; i += 0x8000) s += String.fromCharCode.apply(null, b.subarray(i, i + 0x8000));
  return btoa(s);
}
const cut = (s, n) => { s = s || ""; return s.length <= n ? s : s.slice(0, n - 1) + "…"; };
const size = o => JSON.stringify(o).length;

// 卫星图：Worker 每 30 分钟存到 facet-live 的 5 张 JPEG；一两 KB 的是夜间或来源暂缺的空白图
export async function hubImg() {
  const img = { at: new Date(Math.floor(Date.now() / 600e3) * 600e3).toISOString().slice(0, 19) + "Z", blank: [] };
  await Promise.all(["himawari_vis", "himawari_ir", "himawari_am", "meteosat_natural", "meteosat_snow"].map(async k => {
    try { const b = await (await raw("img/" + k + ".jpg", "facet-live", 300)).arrayBuffer(); if (b.byteLength < 3000) img.blank.push(k); img[k] = "data:image/jpeg;base64," + b64(b); }
    catch (e) { /* 缺一张就不放 */ }
  }));
  return img;
}

// 摄像头：目录来自 hazards/webcams.json；在播的 YouTube 用 Worker 每 10 分钟取的缩略图（rt.sources.cams），其余用目录里存的小图
export async function hubCam(rt) {
  const wc = await j("hazards/webcams.json", "events", 300), live = {};
  for (const c of ((((rt || {}).sources || {}).cams || {}).v || {}).list || []) if (c.img) live[c.id] = c;
  const list = await Promise.all((wc.cams || []).map(async c => {
    const x = {}; for (const k of ["id", "kind", "title", "operator", "url", "channel", "live", "last_image", "fetched", "note"]) x[k] = c[k] ?? null;
    if (live[c.id]) { x.img = live[c.id].img; x.fetched = live[c.id].fetched; }
    else if (c.file && (c.bytes || 0) <= 60000) { try { x.img = "data:image/jpeg;base64," + b64(await (await raw(c.file, "events", 600)).arrayBuffer()); } catch (e) {} }
    return x;
  }));
  return { updated: wc.updated, list };
}

// 外部工具库目录（tools/catalog.py）
export async function hubLib() {
  const cat = await j("hazards/catalog.json", "events", 600);
  const pick = (o, ks) => Object.fromEntries(ks.map(k => [k, o[k] ?? null]));
  const lib = { updated: cat.updated,
    skills: (cat.skills || []).map(s => pick(s, ["name", "desc", "url", "raw", "src", "license"])),
    plugins: (cat.plugins || []).map(p => pick(p, ["name", "desc", "cat", "src", "repo", "url", "install"])),
    mcp: (cat.mcp || []).map(m => pick(m, ["name", "title", "desc", "version", "repo", "remote", "pkg", "site"])) };
  while (size(lib) > 225000 && lib.mcp.length) lib.mcp = lib.mcp.slice(0, Math.floor(lib.mcp.length * 0.8));
  return lib;
}

// 281 种灾害的文献与可用来源（venues.json + scan.json）
export async function hubLit() {
  const [ven, sc] = await Promise.all([j("hazards/venues.json", "events", 1800), j("hazards/scan.json", "events", 600)]);
  const src = {}; for (const h of sc.hazards || []) src[h.code] = [h.sources || [], h.tested_ok || []];
  const build = (nv, np, tl) => (ven.hazards || []).map(h => ({ c: h.code, q: h.query, n: h.papers_2020,
    v: (h.top_venues || h.most_active || []).slice(0, nv).map(x => [x.name, x.h, x.url, x.oa ? 1 : 0]),
    m: (h.multidisciplinary || []).slice(0, 2).map(x => x.name),
    d: (h.data_papers || []).slice(0, np).map(x => [cut(x.title, tl), x.doi, x.year, x.journal]),
    p: (h.top_papers || []).slice(0, np).map(x => [cut(x.title, tl), x.doi, x.year, x.cites, x.journal || x.venue]),
    s: src[h.code] || [[], []] }));
  let lit;
  for (const [nv, np, tl] of [[5, 3, 140], [4, 3, 110], [3, 2, 100], [3, 2, 80], [2, 1, 80]]) {
    lit = { generated: ven.generated, method: ven.method, done: ven.done, total: ven.total, h: build(nv, np, tl) };
    if (size(lit) < 235000) break;
  }
  return lit;
}

// 运行记录 + InSAR 管线 + 卫星过境 + MiroFish，和设备在线状态：hazards 工作流写的小文件
export const hubOps = () => j("hub/ops.json", "events", 120);
export const hubMon = () => j("hub/mt_monitor.json", "events", 120);

// 一次取多份，单份失败不影响其他；附上每份的错误，便于自检
export async function hubAll(parts) {
  const out = {}, err = {};
  await Promise.all(Object.entries(parts).map(async ([k, f]) => { try { out[k] = await f(); } catch (e) { err[k] = String(e && e.message || e).slice(0, 120); } }));
  if (Object.keys(err).length) out.err = err;
  return out;
}
