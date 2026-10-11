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

// 对一景影像的一个坡面求 VV 统计（Data API 对 FeatureCollection 返回 500，只能逐个坡面请求，约 0.25 s/个）
export async function facetStat(itemId, feature) {
  const qs = new URLSearchParams({ collection: "sentinel-1-rtc", item: itemId, assets: "vv", histogram_bins: "1" });
  const body = { type: "Feature", properties: { id: feature.properties.id }, geometry: feature.geometry };
  const r = await fetch(`${DATA}?${qs}`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) });
  const text = await r.text();
  if (!r.ok) throw new Error(`stats ${r.status} ${text.slice(0, 160)}`);
  const s = Object.values(JSON.parse(text).properties.statistics || {})[0];
  return s && s.count > 0 ? { mean_lin: s.mean, db: s.mean > 0 ? 10 * Math.log10(s.mean) : null, count: s.count, valid_percent: s.valid_percent } : null;
}

// 并发跑一组坡面（试算用；Worker 里每次调用最多 50 个子请求）
export async function facetStats(itemId, features, conc = 6) {
  const res = {}; let i = 0, err = 0;
  async function worker() { while (i < features.length) { const f = features[i++]; try { res[f.properties.id] = await facetStat(itemId, f) } catch (e) { err++; res[f.properties.id] = null } } }
  await Promise.all(Array.from({ length: conc }, worker));
  return { res, err };
}
