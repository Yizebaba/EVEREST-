// Planetary Computer 访问层（Cloudflare Worker 与试算共用）。计算在微软 Data API 上完成，这里只发请求、收结果。
export const STAC = "https://planetarycomputer.microsoft.com/api/stac/v1/search";
export const DATA = "https://planetarycomputer.microsoft.com/api/data/v1/item/statistics";

export async function searchScenes({ bbox, start, end, pass = "descending", limit = 250 }) {
  const out = [];
  let body = {
    collections: ["sentinel-1-rtc"], bbox, datetime: `${start}/${end}`, limit,
    query: { "sat:orbit_state": { eq: pass } },
    sortby: [{ field: "datetime", direction: "desc" }],
  };
  let url = STAC;
  for (let page = 0; page < 20; page++) {
    const r = await fetch(url, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) });
    if (!r.ok) throw new Error(`STAC ${r.status} ${(await r.text()).slice(0, 200)}`);
    const j = await r.json();
    for (const f of j.features) out.push({
      id: f.id, t: f.properties.datetime, orbit: f.properties["sat:relative_orbit"],
      platform: f.properties.platform, processed: f.properties["s1:processing_datetime"],
    });
    const nx = (j.links || []).find(l => l.rel === "next");
    if (!nx) break;
    url = nx.href; body = nx.body || body; if (nx.merge) body = { ...body, ...nx.body };
  }
  return out;
}

// 对一景影像的一组坡面求 VV 统计。返回 {facet_id: {mean_lin, db, count, valid_percent}}
export async function facetStats(itemId, features, { asset = "vv" } = {}) {
  const fc = { type: "FeatureCollection", features: features.map(f => ({ type: "Feature", properties: { id: f.properties.id }, geometry: f.geometry })) };
  const qs = new URLSearchParams({ collection: "sentinel-1-rtc", item: itemId, assets: asset, histogram_bins: "1" });
  const r = await fetch(`${DATA}?${qs}`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(fc) });
  const text = await r.text();
  if (!r.ok) throw new Error(`stats ${r.status} ${text.slice(0, 300)}`);
  const j = JSON.parse(text);
  const res = {};
  for (const f of j.features || []) {
    const st = f.properties.statistics || {};
    const k = Object.keys(st)[0];
    const s = k ? st[k] : null;
    res[f.properties.id] = s ? { mean_lin: s.mean, db: s.mean > 0 ? 10 * Math.log10(s.mean) : null, count: s.count, valid_percent: s.valid_percent, band: k } : null;
  }
  return { res, bytes: text.length };
}
