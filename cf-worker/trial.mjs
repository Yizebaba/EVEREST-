// 一次性试算：用与 Worker 相同的代码，取几十个坡面试算速度和结果。写 trial.json。
import fs from "node:fs";
import { searchScenes, facetStats } from "./src/pc.js";
const fc = JSON.parse(fs.readFileSync(new URL("../facets/everest_facets.geojson", import.meta.url)));
const BBOX = [86.54, 27.746, 87.257, 28.23];
const out = { t: new Date().toISOString(), steps: [] };
const step = (k, v) => { const x = { k, ...v }; out.steps.push(x); console.log(JSON.stringify(x).slice(0, 400)); };
try {
  let t0 = Date.now();
  const desc = await searchScenes({ bbox: BBOX, start: "2020-01-01T00:00:00Z", end: new Date().toISOString(), pass: "descending" });
  step("stac_desc", { n: desc.length, ms: Date.now() - t0, newest: desc.slice(0, 5), oldest: desc.slice(-2), orbits: [...new Set(desc.map(d => d.orbit))], platforms: [...new Set(desc.map(d => d.platform))] });
  t0 = Date.now();
  const asc = await searchScenes({ bbox: BBOX, start: "2026-06-01T00:00:00Z", end: new Date().toISOString(), pass: "ascending" });
  step("stac_asc_2026", { n: asc.length, ms: Date.now() - t0, newest: asc.slice(0, 3), orbits: [...new Set(asc.map(d => d.orbit))] });
  // 延迟：拍摄 → 处理完成
  const lat = desc.slice(0, 20).filter(d => d.processed).map(d => (new Date(d.processed) - new Date(d.t)) / 3600e3);
  step("latency_h", { values: lat.map(x => +x.toFixed(2)) });
  // 选 40 个坡面：OCHA 的 critical/elevated 全部 + 随机 quiet
  const F = fc.features;
  const hot = F.filter(f => ["critical", "elevated"].includes(f.properties.ocha_tier));
  const quiet = F.filter(f => f.properties.ocha_tier === "quiet").slice(0, 40 - hot.length);
  const S = hot.concat(quiet);
  const latest = desc[0];
  for (const [label, set] of [["40", S], ["all376", F]]) {
    t0 = Date.now();
    try { const { res, bytes } = await facetStats(latest.id, set); const vals = Object.values(res).filter(Boolean);
      step("stats_" + label, { item: latest.id, ms: Date.now() - t0, bytes, n: vals.length, sample: Object.entries(res).slice(0, 4) });
      if (label === "40") out.latest40 = res;
    } catch (e) { step("stats_" + label + "_err", { ms: Date.now() - t0, err: String(e).slice(0, 300) }); }
  }
  // 小规模历史：同一相对轨道、同一季节（DOY±12）的历年景，40 个坡面
  const ref = new Date(latest.t), doy = d => Math.floor((Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate()) - Date.UTC(d.getUTCFullYear(), 0, 0)) / 864e5);
  const pool = desc.filter(d => d.orbit === latest.orbit && d.id !== latest.id && Math.min(Math.abs(doy(new Date(d.t)) - doy(ref)), 365 - Math.abs(doy(new Date(d.t)) - doy(ref))) <= 12);
  step("pool", { n: pool.length, ids: pool.map(p => p.t.slice(0, 10)) });
  const hist = {}; t0 = Date.now(); let calls = 0;
  for (const p of pool.slice(0, 14)) {
    try { const { res } = await facetStats(p.id, S); calls++; for (const [k, v] of Object.entries(res)) if (v && v.db != null) (hist[k] ||= []).push([p.t.slice(0, 10), +v.db.toFixed(3)]); }
    catch (e) { step("hist_err", { id: p.id, err: String(e).slice(0, 200) }); }
  }
  step("hist", { calls, ms: Date.now() - t0, per_call_ms: calls ? Math.round((Date.now() - t0) / calls) : null });
  // 简化 z 值（同轨、同季、其他年份），与 OCHA 层级对照
  const cmp = [];
  for (const f of S) {
    const id = f.properties.id, cur = out.latest40 && out.latest40[id], h = (hist[id] || []).filter(x => x[0].slice(0, 4) !== latest.t.slice(0, 4)).map(x => x[1]);
    if (!cur || cur.db == null || h.length < 4) { cmp.push({ id, ocha: f.properties.ocha_tier, z: null, n: h.length }); continue; }
    const m = h.reduce((a, b) => a + b, 0) / h.length, sd = Math.sqrt(h.reduce((a, b) => a + (b - m) ** 2, 0) / (h.length - 1));
    cmp.push({ id, ocha: f.properties.ocha_tier, ocha_live: f.properties.ocha_live, db: +cur.db.toFixed(2), clim: +m.toFixed(2), sd: +sd.toFixed(2), z: +((cur.db - m) / sd).toFixed(2), n: h.length, valid: cur.valid_percent });
  }
  out.compare = cmp; out.hist = hist;
  step("compare", { n: cmp.length, with_z: cmp.filter(c => c.z != null).length });
} catch (e) { step("fatal", { err: String(e.stack || e).slice(0, 500) }); }
fs.writeFileSync("trial.json", JSON.stringify(out, null, 1));
