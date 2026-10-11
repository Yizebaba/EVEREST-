// 试算：40 个坡面 × (最新降轨景 + 同轨同季节历年景)，测速度并算简化 z 值，与 OCHA 9/3 层级对照。
import fs from "node:fs";
import { searchScenes, facetStats } from "./src/pc.js";
const fc = JSON.parse(fs.readFileSync(new URL("../facets/everest_facets.geojson", import.meta.url)));
const BBOX = [86.54, 27.746, 87.257, 28.23];
const out = { t: new Date().toISOString(), steps: [] };
const step = (k, v) => { const x = { k, ...v }; out.steps.push(x); console.log(JSON.stringify(x).slice(0, 400)); };
const doy = d => Math.floor((Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate()) - Date.UTC(d.getUTCFullYear(), 0, 0)) / 864e5);
const F = fc.features;
const S = F.filter(f => ["critical", "elevated"].includes(f.properties.ocha_tier)).concat(F.filter(f => f.properties.ocha_tier === "quiet").slice(0, 20));
const desc = await searchScenes({ bbox: BBOX, start: "2020-01-01T00:00:00Z", end: new Date().toISOString(), pass: "descending" });
const latest = desc[0], ref = new Date(latest.t);
// 同一天可能有两景（相邻帧），按日期去重，优先第一景
const seen = new Set();
const pool = desc.filter(d => d.orbit === latest.orbit && d.id !== latest.id && d.t.slice(0, 4) !== latest.t.slice(0, 4)
  && Math.min(Math.abs(doy(new Date(d.t)) - doy(ref)), 365 - Math.abs(doy(new Date(d.t)) - doy(ref))) <= 12)
  .filter(d => { const k = d.t.slice(0, 10); if (seen.has(k)) return false; seen.add(k); return true; });
step("plan", { facets: S.length, latest: latest.id, latest_t: latest.t, processed: latest.processed, pool: pool.map(p => p.t.slice(0, 10)) });
let t0 = Date.now();
const cur = await facetStats(latest.id, S);
step("latest", { ms: Date.now() - t0, per_req_ms: Math.round((Date.now() - t0) / S.length * 6), err: cur.err, ok: Object.values(cur.res).filter(Boolean).length });
const hist = {}; t0 = Date.now(); let req = 0, errs = 0;
for (const p of pool) {
  const r = await facetStats(p.id, S); req += S.length; errs += r.err;
  for (const [k, v] of Object.entries(r.res)) if (v && v.db != null) (hist[k] ||= []).push([p.t.slice(0, 10), +v.db.toFixed(3), v.count]);
}
step("history", { scenes: pool.length, requests: req, errors: errs, ms: Date.now() - t0, req_per_s: +(req / ((Date.now() - t0) / 1000)).toFixed(1) });
// 区域对照：同一景所有坡面 z 的中位数（与 OCHA 一致的做法）
const rows = [];
for (const f of S) {
  const id = f.properties.id, c = cur.res[id], h = (hist[id] || []).map(x => x[1]);
  if (!c || c.db == null || h.length < 4) { rows.push({ id, ocha: f.properties.ocha_tier, z: null, n: h.length }); continue; }
  const m = h.reduce((a, b) => a + b, 0) / h.length, sd = Math.sqrt(h.reduce((a, b) => a + (b - m) ** 2, 0) / (h.length - 1));
  rows.push({ id, ocha: f.properties.ocha_tier, ocha_live: f.properties.ocha_live, db: +c.db.toFixed(2), clim: +m.toFixed(2), sd: +sd.toFixed(2), z: +((c.db - m) / sd).toFixed(2), n: h.length, px: c.count });
}
const zs = rows.filter(r => r.z != null).map(r => r.z).sort((a, b) => a - b), med = zs.length ? zs[Math.floor(zs.length / 2)] : 0;
rows.forEach(r => { if (r.z != null) r.z_adj = +(r.z - med).toFixed(2) });
out.compare = rows; out.hist = hist; out.region_median_z = med;
step("compare", { with_z: zs.length, region_median_z: med });
fs.writeFileSync("trial.json", JSON.stringify(out, null, 1));
