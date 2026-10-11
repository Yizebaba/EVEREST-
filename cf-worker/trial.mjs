// 试算第 2 步：找出 Data API statistics 接受的请求格式（单景、单坡面），再小规模算。
import fs from "node:fs";
import { DATA } from "./src/pc.js";
const fc = JSON.parse(fs.readFileSync(new URL("../facets/everest_facets.geojson", import.meta.url)));
const out = { t: new Date().toISOString(), steps: [] };
const step = (k, v) => { const x = { k, ...v }; out.steps.push(x); console.log(JSON.stringify(x).slice(0, 500)); };
const item = "S1D_IW_GRDH_1SDV_20261006T001038_20261006T001103_004887_009321_rtc";
const f1 = fc.features[0], feat = { type: "Feature", properties: { id: f1.properties.id }, geometry: f1.geometry };
const fc3 = { type: "FeatureCollection", features: fc.features.slice(0, 3).map(f => ({ type: "Feature", properties: { id: f.properties.id }, geometry: f.geometry })) };
async function tryit(name, qs, body, method = "POST") {
  const t0 = Date.now();
  try {
    const r = await fetch(`${qs.__info ? "" : ""}${DATA}?${new URLSearchParams(qs)}`, method === "POST" ? { method, headers: { "content-type": "application/json" }, body: JSON.stringify(body) } : {});
    const t = await r.text();
    step(name, { status: r.status, ms: Date.now() - t0, bytes: t.length, head: t.slice(0, 350) });
  } catch (e) { step(name, { err: String(e).slice(0, 200) }); }
}
const base = { collection: "sentinel-1-rtc", item };
await tryit("get_whole_vv", { ...base, assets: "vv", max_size: "256" }, null, "GET");
await tryit("info", { ...base }, null, "GET");
await tryit("post_feature_vv", { ...base, assets: "vv" }, feat);
await tryit("post_feature_vv_maxsize", { ...base, assets: "vv", max_size: "1024" }, feat);
await tryit("post_wrapped", { ...base, assets: "vv" }, { geojson: feat });
await tryit("post_fc3", { ...base, assets: "vv" }, fc3);
await tryit("post_feature_expr", { ...base, expression: "vv", asset_as_band: "true" }, feat);
await tryit("post_feature_vv_b1", { ...base, assets: "vv", asset_bidx: "vv|1" }, feat);
fs.writeFileSync("trial.json", JSON.stringify(out, null, 1));
