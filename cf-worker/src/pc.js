// Planetary Computer 访问层（Cloudflare Worker 与试算共用）。计算在微软 Data API 上完成，这里只发请求、收结果。
// 基础地址可用环境变量 PC_STAC / PC_DATA 覆盖（本地测试指向模拟服务）。
export const STAC = "https://planetarycomputer.microsoft.com/api/stac/v1/search";
export const DATA = "https://planetarycomputer.microsoft.com/api/data/v1/item/statistics";

export async function searchScenes({ bbox, start, end, pass = "descending", limit = 250, stac = STAC, maxPages = 20 }) {
  const out = [];
  let body = {
    collections: ["sentinel-1-rtc"], bbox, datetime: `${start}/${end}`, limit,
    query: { "sat:orbit_state": { eq: pass } },
    sortby: [{ field: "datetime", direction: "desc" }],
  };
  let url = stac, pages = 0;
  for (; pages < maxPages; pages++) {
    const r = await fetch(url, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) });
    if (!r.ok) throw new Error(`STAC ${r.status} ${(await r.text()).slice(0, 200)}`);
    const j = await r.json();
    for (const f of j.features) out.push({
      id: f.id, t: f.properties.datetime, orbit: f.properties["sat:relative_orbit"],
      platform: f.properties.platform, processed: f.properties["s1:processing_datetime"] || null,
    });
    const nx = (j.links || []).find(l => l.rel === "next");
    if (!nx) break;
    url = nx.href; body = nx.merge ? { ...body, ...(nx.body || {}) } : (nx.body || body);
  }
  return { scenes: out, pages: pages + 1 };
}

// 一景影像的一个坡面：VV（γ0，线性）统计。Data API 对 FeatureCollection 返回 500，只能逐个坡面请求。
// 返回 null 表示坡面不在这一景里（无像元）。
export async function facetStat(itemId, id, ring, { data = DATA } = {}) {
  const qs = new URLSearchParams({ collection: "sentinel-1-rtc", item: itemId, assets: "vv", histogram_bins: "1" });
  const body = { type: "Feature", properties: { id }, geometry: { type: "Polygon", coordinates: [ring] } };
  const r = await fetch(`${data}?${qs}`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) });
  const text = await r.text();
  if (!r.ok) throw new Error(`stats ${r.status}`);
  const s = Object.values(JSON.parse(text).properties?.statistics || {})[0];
  return s && s.count > 0 && s.mean > 0 ? { db: 10 * Math.log10(s.mean), px: Math.round(s.count) } : null;
}

// 试算脚本用：并发跑一组 GeoJSON 坡面
export async function facetStats(itemId, features, conc = 6) {
  const res = {}; let i = 0, err = 0;
  async function worker() {
    while (i < features.length) {
      const f = features[i++];
      try { res[f.properties.id] = await facetStat(itemId, f.properties.id, f.geometry.coordinates[0]); }
      catch { err++; res[f.properties.id] = null; }
    }
  }
  await Promise.all(Array.from({ length: conc }, worker));
  return { res, err };
}
