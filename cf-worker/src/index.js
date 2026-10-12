// 珠峰冰坡雷达亮度监测（Cloudflare Worker，每分钟一次）。
// 方法照搬 OCHA-DAP 0005 facet watch（MIT），数据换成 Planetary Computer Sentinel-1 RTC（γ0，地形校正），
// 计算在微软 Data API 和 Cloudflare D1 上完成；本 Worker 只做调度、记账和对外发布。
// 只监测：每个坡面“和自己历年同季相比有多反常”的排名，不预测、不判断会不会崩。
import FACETS from "./facets.json";
import { searchScenes, facetStat, STAC, DATA } from "./pc.js";
import { rtTick, rtPublic, IMG } from "./rt.js";

const BBOX = [86.54, 27.746, 87.257, 28.23];
const START = "2020-01-01T00:00:00Z";
const PER_TICK = 40;            // 每次最多 40 个子请求给微软（免费版上限 50）
const CONC = 6;
const DOY_WIN = 12, MIN_POOL = 10, MIN_FACE_DATE = 30, RUN_LEN = 3;
const SEASON = [152, 237];      // 6/1–8/25，OCHA 的历史对照季
const TIERS = [[1, "critical"], [5, "elevated"], [15, "watch"], [100, "quiet"]];
const IDRE = /^[A-Za-z0-9_]+$/;

const SCHEMA = [
  `CREATE TABLE IF NOT EXISTS scene (id TEXT PRIMARY KEY, t TEXT, date TEXT, orbit INTEGER, platform TEXT, processed TEXT,
     added TEXT, next_idx INTEGER DEFAULT 0, retry TEXT DEFAULT '[]', rounds INTEGER DEFAULT 0, status TEXT DEFAULT 'queued', done_at TEXT)`,
  `CREATE TABLE IF NOT EXISTS obs (date TEXT, orbit INTEGER, facet_id TEXT, t TEXT, year INTEGER, doy INTEGER, db REAL, px INTEGER,
     z_adj REAL, PRIMARY KEY (date, orbit, facet_id))`,
  `CREATE INDEX IF NOT EXISTS obs_fod ON obs (facet_id, orbit, doy)`,
  `CREATE TABLE IF NOT EXISTS fmax (facet_id TEXT, orbit INTEGER, maxpx INTEGER, PRIMARY KEY (facet_id, orbit))`,
  `CREATE TABLE IF NOT EXISTS scored (date TEXT, orbit INTEGER, at TEXT, n INTEGER, PRIMARY KEY (date, orbit))`,
  `CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT)`,
];

const nowIso = () => new Date().toISOString();
const doyOf = t => { const d = new Date(t); return Math.floor((Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate()) - Date.UTC(d.getUTCFullYear(), 0, 0)) / 864e5); };
const num = x => (Number.isFinite(x) ? String(Math.round(x * 1e4) / 1e4) : "NULL");
const q = s => { if (!IDRE.test(String(s))) throw new Error("bad id " + s); return `'${s}'`; };
const qs = s => `'${String(s).replace(/[^0-9A-Za-z:.\-T_Z+]/g, "")}'`;

async function getMeta(env, k) { const r = await env.DB.prepare("SELECT v FROM meta WHERE k=?").bind(k).first(); return r ? r.v : null; }
async function setMeta(env, k, v) { await env.DB.prepare("INSERT INTO meta (k,v) VALUES (?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v").bind(k, v).run(); }

async function init(env) {
  if (await getMeta(env, "schema").catch(() => null) === "1") return;
  await env.DB.batch(SCHEMA.map(s => env.DB.prepare(s)));
  await setMeta(env, "schema", "1");
}

// 1 发现新影像（降轨，与 OCHA 一致）：首次全量回填 2020 年至今，之后每 30 分钟查一次最近 5 天
async function discover(env, log) {
  const last = await getMeta(env, "last_search");
  if (last && Date.now() - Date.parse(last) < 30 * 60e3) return;
  const newest = await env.DB.prepare("SELECT MAX(t) t FROM scene").first();
  const start = newest && newest.t ? new Date(Date.parse(newest.t) - 5 * 864e5).toISOString() : START;
  const { scenes, pages } = await searchScenes({ bbox: BBOX, start, end: nowIso(), stac: env.PC_STAC || STAC, maxPages: 6 });
  log.fetches += pages;
  const rows = scenes.filter(s => IDRE.test(s.id) && Number.isInteger(s.orbit));
  if (rows.length) {
    const vals = rows.map(s => `(${q(s.id)},${qs(s.t)},${qs(s.t.slice(0, 10))},${s.orbit},${q(s.platform.replace(/-/g, "_"))},${s.processed ? qs(s.processed) : "NULL"},${qs(nowIso())})`);
    await env.DB.prepare(`INSERT OR IGNORE INTO scene (id,t,date,orbit,platform,processed,added) VALUES ${vals.join(",")}`).run();
  }
  await setMeta(env, "last_search", nowIso());
  log.discovered = rows.length;
}

// 2 处理一景：最新的优先（实时），然后往回补历史
async function work(env, log) {
  const sc = await env.DB.prepare("SELECT * FROM scene WHERE status='queued' ORDER BY t DESC LIMIT 1").first();
  if (!sc) return false;
  const N = Math.min(FACETS.length, Number(env.FACET_LIMIT || FACETS.length));
  // 先按顺序走完全部坡面，再补做失败的（失败的放进 retry 列表）
  let idx = [];
  const retry = JSON.parse(sc.retry || "[]");
  const PT = Number(env.PER_TICK || PER_TICK);
  // 同一天相邻帧：已经有像元的坡面不再请求
  const have = new Set((await env.DB.prepare("SELECT facet_id FROM obs WHERE date=? AND orbit=?").bind(sc.date, sc.orbit).all()).results.map(r => r.facet_id));
  let ni = sc.next_idx;
  for (; ni < N && idx.length < PT; ni++) if (!have.has(FACETS[ni].id)) idx.push(ni);
  const nextIdx = ni;
  let retryLeft = retry;
  if (idx.length < PT && nextIdx >= N && retry.length) { const k = PT - idx.length; idx = idx.concat(retry.slice(0, k)); retryLeft = retry.slice(k); }
  const res = [], fail = [];
  let p = 0;
  const opt = { data: env.PC_DATA || DATA };
  await Promise.all(Array.from({ length: CONC }, async () => {
    while (p < idx.length) {
      const i = idx[p++], f = FACETS[i];
      try { const s = await facetStat(sc.id, f.id, f.g, opt); if (s) res.push([f.id, s]); }
      catch { fail.push(i); }
    }
  }));
  log.fetches += idx.length; log.scene = sc.id; log.ok = res.length; log.fail = fail.length;
  const year = Number(sc.date.slice(0, 4)), doy = doyOf(sc.t);
  const stmts = [];
  if (res.length) {
    const vals = res.map(([id, s]) => `(${qs(sc.date)},${sc.orbit},${q(id)},${qs(sc.t)},${year},${doy},${num(s.db)},${s.px})`);
    // 同一天相邻两帧都覆盖到的坡面：保留像元多的那一帧
    stmts.push(env.DB.prepare(`INSERT INTO obs (date,orbit,facet_id,t,year,doy,db,px) VALUES ${vals.join(",")}
      ON CONFLICT(date,orbit,facet_id) DO UPDATE SET db=excluded.db, px=excluded.px, t=excluded.t WHERE excluded.px > obs.px`));
  }
  const rounds = sc.rounds + 1;
  const newRetry = retryLeft.concat(fail);
  // 失败的坡面最多补 3 轮（每轮最多 PER_TICK 个），之后放弃，避免卡死
  const finished = nextIdx >= N && (newRetry.length === 0 || rounds > Math.ceil(N / PT) + 3);
  stmts.push(env.DB.prepare("UPDATE scene SET next_idx=?, retry=?, rounds=?, status=?, done_at=? WHERE id=?")
    .bind(nextIdx, JSON.stringify(finished ? [] : newRetry), rounds, finished ? "done" : "queued", finished ? nowIso() : null, sc.id));
  await env.DB.batch(stmts);
  if (finished) log.scene_done = sc.id;
  return true;
}

// 3 给一个日期（同轨）算 z：同坡面、同轨、其他年份、同季（±12 天）的均值和标准差；减去当景所有坡面 z 的中位数（区域对照）
async function scoreOne(env, log) {
  const d = await env.DB.prepare(`SELECT o.date, o.orbit, MIN(o.t) t FROM obs o LEFT JOIN scored s ON s.date=o.date AND s.orbit=o.orbit
     WHERE s.date IS NULL GROUP BY o.date, o.orbit ORDER BY o.date LIMIT 1`).first();
  if (!d) return false;
  // 每个坡面的满覆盖像元数（OCHA：像元 < 80% 的景视为部分覆盖，不用）。每批新影像后重建一次，省写入额度
  const lastDone = (await env.DB.prepare("SELECT MAX(done_at) a FROM scene").first()).a || "";
  if ((await getMeta(env, "fmax_at") || "") < lastDone) {
    await env.DB.batch([env.DB.prepare("DELETE FROM fmax"), env.DB.prepare("INSERT INTO fmax SELECT facet_id, orbit, MAX(px) FROM obs GROUP BY facet_id, orbit")]);
    await setMeta(env, "fmax_at", nowIso());
  }
  const doy = doyOf(d.t), year = Number(d.date.slice(0, 4));
  const lo = doy - DOY_WIN, hi = doy + DOY_WIN;
  const win = lo < 1 ? `(o.doy >= ${lo + 365} OR o.doy <= ${hi})` : hi > 365 ? `(o.doy >= ${lo} OR o.doy <= ${hi - 365})` : `o.doy BETWEEN ${lo} AND ${hi}`;
  const r = await env.DB.prepare(`
    WITH cur AS (SELECT c.facet_id, c.db FROM obs c JOIN fmax f ON f.facet_id=c.facet_id AND f.orbit=c.orbit
                 WHERE c.date=?1 AND c.orbit=?2 AND c.px >= 0.8*f.maxpx)
    SELECT cur.facet_id, cur.db, AVG(o.db) m, AVG(o.db*o.db) m2, COUNT(*) n
      FROM cur JOIN obs o ON o.facet_id=cur.facet_id AND o.orbit=?2 AND o.year<>?3 AND ${win}
      JOIN fmax f ON f.facet_id=o.facet_id AND f.orbit=o.orbit AND o.px >= 0.8*f.maxpx
     GROUP BY cur.facet_id HAVING n >= ${MIN_POOL}`).bind(d.date, d.orbit, year).all();
  const z = [];
  for (const x of r.results) {
    const v = (x.m2 - x.m * x.m) * x.n / (x.n - 1);
    if (v > 0) z.push([x.facet_id, (x.db - x.m) / Math.sqrt(v)]);
  }
  const stmts = [];
  if (z.length >= MIN_FACE_DATE) {
    const s = z.map(a => a[1]).sort((a, b) => a - b), med = s[Math.floor(s.length / 2)];
    const cases = z.map(([id, v]) => `WHEN ${q(id)} THEN ${num(v - med)}`).join(" ");
    stmts.push(env.DB.prepare(`UPDATE obs SET z_adj = CASE facet_id ${cases} ELSE NULL END WHERE date=? AND orbit=?`).bind(d.date, d.orbit));
  }
  stmts.push(env.DB.prepare("INSERT OR REPLACE INTO scored (date,orbit,at,n) VALUES (?,?,?,?)").bind(d.date, d.orbit, nowIso(), z.length));
  await env.DB.batch(stmts);
  log.scored = `${d.date}/${d.orbit} n=${z.length}`;
  return true;
}

// 4 汇总：历年同季最反常 3 连景（历史零分布）和最近 90 天最反常 3 连景（现在），按历史分位分级
async function rollup(env, log) {
  const lastT = (await env.DB.prepare("SELECT MAX(t) t FROM obs WHERE z_adj IS NOT NULL").first()).t;
  if (!lastT) return;
  const runSql = where => `SELECT facet_id, year, MIN(rmax) s FROM (
      SELECT facet_id, year, MAX(z_adj) OVER w rmax, COUNT(*) OVER w c FROM obs WHERE z_adj IS NOT NULL AND ${where}
      WINDOW w AS (PARTITION BY facet_id, year ORDER BY t ROWS BETWEEN CURRENT ROW AND ${RUN_LEN - 1} FOLLOWING))
    WHERE c=${RUN_LEN} GROUP BY facet_id, year`;
  const curYear = Number(lastT.slice(0, 4));
  const seas = (await env.DB.prepare(runSql(`doy BETWEEN ${SEASON[0]} AND ${SEASON[1]}`)).all()).results;
  const cut = new Date(Date.parse(lastT) - 90 * 864e5).toISOString();
  const live = (await env.DB.prepare(`SELECT facet_id, MIN(rmax) s FROM (
      SELECT facet_id, MAX(z_adj) OVER w rmax, COUNT(*) OVER w c FROM obs WHERE z_adj IS NOT NULL AND t >= ?
      WINDOW w AS (PARTITION BY facet_id ORDER BY t ROWS BETWEEN CURRENT ROW AND ${RUN_LEN - 1} FOLLOWING))
    WHERE c=${RUN_LEN} GROUP BY facet_id`).bind(cut).all()).results;
  const last = (await env.DB.prepare("SELECT facet_id, z_adj, date FROM obs WHERE t >= ? AND z_adj IS NOT NULL ORDER BY t").bind(cut).all()).results;
  const nul = seas.filter(x => x.year < curYear).map(x => x.s).sort((a, b) => a - b);
  const years = {}, lastZ = {};
  for (const x of seas) (years[x.facet_id] ||= {})[x.year] = Math.round(x.s * 100) / 100;
  for (const x of last) lastZ[x.facet_id] = [x.date, Math.round(x.z_adj * 100) / 100];
  const lv = Object.fromEntries(live.map(x => [x.facet_id, x.s]));
  const counts = { critical: 0, elevated: 0, watch: 0, quiet: 0, nodata: 0 };
  const out = FACETS.map(f => {
    const s = lv[f.id];
    let tier = "nodata", pct = null;
    if (s != null && nul.length >= 100) {
      let k = 0; while (k < nul.length && nul[k] <= s) k++;
      pct = Math.round(1000 * k / nul.length) / 10;
      tier = TIERS.find(([lim]) => pct < lim || lim === 100)[1];
    }
    counts[tier]++;
    return { id: f.id, tier, live: s == null ? null : Math.round(s * 100) / 100, pct, years: years[f.id] || {}, last: lastZ[f.id] || null };
  });
  const sc = await env.DB.prepare("SELECT COUNT(*) n, SUM(status='done') d, MAX(CASE WHEN status='done' THEN t END) lt, MAX(CASE WHEN status='done' THEN processed END) lp FROM scene").first();
  const doc = {
    generated: nowIso(), last_scene: lastT, last_processed: sc.lp, scenes_done: sc.d, scenes_total: sc.n,
    null_n: nul.length, tiers: counts, facets: out,
    method: "OCHA-DAP 0005 facet watch (MIT): leave-one-out same-season z per orbit, minus same-scene median; worst 3-consecutive; tier = percentile vs 2020–previous-year Jun–Aug null. Data: Sentinel-1 RTC (γ0 VV, descending) via Microsoft Planetary Computer.",
    note: "只监测：排名表示“和自己历年同季相比有多反常”，不预测、不是预警。",
  };
  await setMeta(env, "live", JSON.stringify(doc));
  await setMeta(env, "live_at", nowIso());
  log.rollup = counts;
  return doc;
}

// 5 （可选）把结果推到 GitHub 仓库的 facet-live 分支，让平台页面接入。需要在 Cloudflare 里配 GH_TOKEN 密钥。
async function pushFile(env, path, obj, msg, log) {
  if (!env.GH_TOKEN || !env.GH_REPO) return null;
  const api = `https://api.github.com/repos/${env.GH_REPO}`, br = env.GH_BRANCH || "facet-live";
  const h = { authorization: `Bearer ${env.GH_TOKEN}`, accept: "application/vnd.github+json", "user-agent": "everest-facets-worker", "content-type": "application/json" };
  const ref = await fetch(`${api}/git/ref/heads/${br}`, { headers: h }); log.fetches++;
  if (ref.status === 404) {
    const base = await (await fetch(`${api}/git/ref/heads/${env.GH_BASE || "data-probe"}`, { headers: h })).json(); log.fetches++;
    const c = await fetch(`${api}/git/refs`, { method: "POST", headers: h, body: JSON.stringify({ ref: `refs/heads/${br}`, sha: base.object.sha }) }); log.fetches++;
    log.gh_branch = c.status;
  } else if (!ref.ok) { log.github = ref.status; return ref.status; }
  const cur = await fetch(`${api}/contents/${path}?ref=${br}`, { headers: h }); log.fetches++;
  const sha = cur.ok ? (await cur.json()).sha : undefined;
  const bytes = obj instanceof Uint8Array ? obj : new TextEncoder().encode(JSON.stringify(obj));
  let bin = ""; for (let i = 0; i < bytes.length; i += 0x8000) bin += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
  const r = await fetch(`${api}/contents/${path}`, { method: "PUT", headers: h, body: JSON.stringify({ message: msg, content: btoa(bin), branch: br, sha }) }); log.fetches++;
  log.github = r.status;
  return r.status;
}

async function pushGitHub(env, doc, log) {
  const st = await pushFile(env, "facet_live.json", doc, `facet live ${doc.last_scene}`, log);
  if (st === 200 || st === 201) await setMeta(env, "pushed_scene", `${doc.last_scene}|${doc.null_n}`);
}

// 每小时把进度也推一次（建基线期间平台能显示进度；也顺便检查 GH_TOKEN 是否可用）
async function pushStatus(env, log) {
  if (!env.GH_TOKEN) return false;
  const last = await getMeta(env, "gh_status_at");
  if (last && Date.now() - Date.parse(last) < 60 * 60e3) return false;
  await setMeta(env, "gh_status_at", nowIso());
  const st = await status(env);
  delete st.last_tick;
  log.gh_status = await pushFile(env, "facet_status.json", { t: nowIso(), ...st }, `facet status ${nowIso().slice(0, 16)}`, log);
  const rt = await getMeta(env, "rt");
  if (rt) log.gh_rt = await pushFile(env, "rt.json", rtPublic(JSON.parse(rt)), `rt ${nowIso().slice(0, 16)}`, log);
  // 卫星图像每 3 小时存一张到 GitHub（平台页面不能直接加载外部图片）
  const li = await getMeta(env, "gh_img_at");
  if (!li || Date.now() - Date.parse(li) > 3 * 3600e3) {
    await setMeta(env, "gh_img_at", nowIso());
    for (const [k, path] of [["himawari_vis", "img/himawari_vis.png"], ["meteosat_snow", "img/meteosat_snow.png"]]) {
      try { const r = await fetch(IMG[k]); log.fetches++; if (r.ok) log["gh_" + k] = await pushFile(env, path, new Uint8Array(await r.arrayBuffer()), `img ${k} ${nowIso().slice(0, 16)}`, log); }
      catch (e) { log["gh_" + k] = String(e).slice(0, 80); }
    }
  }
  return true;
}

async function tick(env) {
  const log = { t: nowIso(), fetches: 0 };
  try {
    await init(env);
    if (new Date().getUTCMinutes() % 5 === 2 || env.RT_EVERY_TICK === "1") {
      Object.assign(log, await rtTick(env, getMeta, setMeta));
      await setMeta(env, "last_tick", JSON.stringify(log)); return log;
    }
    await discover(env, log);
    // 推进度的那一分钟不做计算，避免超过每次 50 个子请求
    if (await pushStatus(env, log)) { await setMeta(env, "last_tick", JSON.stringify(log)); return log; }
    const worked = await work(env, log);
    // 队列空了才打分：保证每个日期都在完整历史上计算
    if (!worked) {
      const scored = await scoreOne(env, log);
      if (!scored) {
        const done = await getMeta(env, "live_at"), lastScored = await env.DB.prepare("SELECT MAX(at) a FROM scored").first();
        if (!done || (lastScored.a && lastScored.a > done)) {
          const doc = await rollup(env, log);
          if (doc && (await getMeta(env, "pushed_scene")) !== `${doc.last_scene}|${doc.null_n}`) await pushGitHub(env, doc, log);
        }
      }
    }
  } catch (e) { log.err = String(e && e.stack || e).slice(0, 400); }
  await setMeta(env, "last_tick", JSON.stringify(log)).catch(() => {});
  return log;
}

const CORS = { "access-control-allow-origin": "*", "cache-control": "public, max-age=300" };
const json = (o, s = 200) => new Response(JSON.stringify(o), { status: s, headers: { "content-type": "application/json; charset=utf-8", ...CORS } });

async function status(env) {
  await init(env);
  const s = await env.DB.prepare(`SELECT COUNT(*) n, SUM(status='done') d, MIN(t) first, MAX(t) last,
      MAX(CASE WHEN status='done' THEN t END) last_done FROM scene`).first();
  const o = await env.DB.prepare("SELECT COUNT(*) n FROM obs").first();
  const sc = await env.DB.prepare("SELECT COUNT(*) n FROM scored").first();
  const dates = await env.DB.prepare("SELECT COUNT(*) n FROM (SELECT 1 FROM obs GROUP BY date, orbit)").first();
  return { code: "v4-rt", gh_token_set: !!env.GH_TOKEN, gh_status_at: await getMeta(env, "gh_status_at"), scenes: s, obs_rows: o.n, dates_scored: sc.n, dates_total: dates.n, live_at: await getMeta(env, "live_at"),
    last_tick: JSON.parse((await getMeta(env, "last_tick")) || "null"), facets: FACETS.length };
}

export default {
  async scheduled(controller, env, ctx) { ctx.waitUntil(tick(env)); },
  async fetch(req, env) {
    const u = new URL(req.url);
    if (u.pathname === "/api/live.json") { await init(env); const v = await getMeta(env, "live"); return v ? new Response(v, { headers: { "content-type": "application/json; charset=utf-8", ...CORS } }) : json({ building: true, status: await status(env) }, 202); }
    if (u.pathname === "/api/status.json") return json(await status(env));
    if (u.pathname === "/api/facets.json") return json(FACETS);
    if (u.pathname === "/api/rt.json") { await init(env); const v = await getMeta(env, "rt"); return json(v ? rtPublic(JSON.parse(v)) : { building: true }); }
    if (u.pathname === "/rt") return new Response(RT_PAGE, { headers: { "content-type": "text/html; charset=utf-8" } });
    if (u.pathname === "/__tick" && env.ALLOW_MANUAL_TICK === "1") return json(await tick(env));
    if (u.pathname === "/") return new Response(PAGE, { headers: { "content-type": "text/html; charset=utf-8" } });
    return new Response("not found", { status: 404 });
  },
};

const PAGE = `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>珠峰冰坡雷达监测</title><style>
:root{--bg:#0e1013;--fg:#e8e6e1;--mute:#8d8b86;--line:#2a2d33;--c:#ef6a5a;--e:#e8a33c;--w:#d8cf6a;--q:#5d7f73;--n:#3a3d44}
body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.5 system-ui,-apple-system,"PingFang SC","Noto Sans CJK SC",sans-serif}
main{max-width:1000px;margin:0 auto;padding:16px}h1{font-size:18px;margin:0 0 4px}.sub{color:var(--mute);font-size:12px}
svg{width:100%;height:auto;background:#15181d;border-radius:8px;margin:10px 0}.leg span{display:inline-flex;align-items:center;gap:4px;margin-right:12px;font-size:12px}
.leg i{width:10px;height:10px;border-radius:2px;display:inline-block}table{width:100%;border-collapse:collapse;font-size:12px}td,th{padding:4px;border-bottom:1px solid var(--line);text-align:left}
</style></head><body><main><h1>珠峰冰坡雷达亮度监测</h1><div class="sub" id="meta">加载中…</div>
<div class="leg"><span><i style="background:var(--c)"></i>异常显著（&lt;1%）</span><span><i style="background:var(--e)"></i>偏高（&lt;5%）</span><span><i style="background:var(--w)"></i>留意（&lt;15%）</span><span><i style="background:var(--q)"></i>平静</span><span><i style="background:var(--n)"></i>无数据</span></div>
<svg id="map" viewBox="0 0 1000 680"></svg><table id="tb"></table>
<p class="sub"><a href="/rt" style="color:#8fc3ff">→ 珠峰实时源总览（卫星云图、地震、网络连通、空中交通、灾害警报、DORIS 信标）</a></p><p class="sub">方法：OCHA-DAP 0005 facet watch（MIT），数据：Sentinel-1 RTC（Microsoft Planetary Computer）。只监测：分级表示“和自己历年同季相比有多反常”，不预测、不是预警。</p></main>
<script>
const C={critical:"var(--c)",elevated:"var(--e)",watch:"var(--w)",quiet:"var(--q)",nodata:"var(--n)"},CN={critical:"异常显著",elevated:"偏高",watch:"留意",quiet:"平静",nodata:"无数据"};
const B=[86.54,27.746,87.257,28.23],X=x=>(x-B[0])/(B[2]-B[0])*1000,Y=y=>(B[3]-y)/(B[3]-B[1])*680;
Promise.all([fetch("/api/facets.json").then(r=>r.json()),fetch("/api/live.json").then(r=>r.json())]).then(([F,L])=>{
 const m=document.getElementById("meta");
 if(L.building){const s=L.status;m.textContent="正在建立 2020 年以来的历史基线："+(s.scenes.d||0)+" / "+s.scenes.n+" 景已算，"+s.dates_scored+" / "+s.dates_total+" 个日期已打分。完成后自动出分级。";}
 else m.textContent="最新影像 "+new Date(L.last_scene).toLocaleString("zh-CN",{timeZone:"Asia/Shanghai",hour12:false})+"（北京），微软处理完成 "+(L.last_processed?new Date(L.last_processed).toLocaleString("zh-CN",{timeZone:"Asia/Shanghai",hour12:false}):"—")+"；本页汇总 "+new Date(L.generated).toLocaleString("zh-CN",{timeZone:"Asia/Shanghai",hour12:false})+"。历史分布 "+L.null_n+" 个坡面-季。";
 const T=Object.fromEntries((L.facets||[]).map(f=>[f.id,f]));
 document.getElementById("map").innerHTML=F.map(f=>{const t=(T[f.id]||{}).tier||"nodata";return '<polygon points="'+f.g.map(p=>X(p[0]).toFixed(1)+","+Y(p[1]).toFixed(1)).join(" ")+'" fill="'+C[t]+'" fill-opacity=".85" stroke="#000" stroke-width=".4"><title>'+f.id+" "+CN[t]+'</title></polygon>'}).join("")+'<polygon points="'+X(86.925)+","+(Y(27.988)-9)+" "+(X(86.925)-7)+","+(Y(27.988)+5)+" "+(X(86.925)+7)+","+(Y(27.988)+5)+'" fill="#fff"><title>珠峰</title></polygon>';
 const top=(L.facets||[]).filter(f=>f.tier!=="quiet"&&f.tier!=="nodata").sort((a,b)=>a.pct-b.pct);
 document.getElementById("tb").innerHTML='<tr><th>坡面</th><th>等级</th><th>最近90天</th><th>历史分位</th><th>最新一景</th></tr>'+top.map(f=>'<tr><td>'+f.id+'</td><td style="color:'+C[f.tier]+'">'+CN[f.tier]+'</td><td>'+f.live+'</td><td>'+f.pct+'%</td><td>'+(f.last?f.last[0]+" "+f.last[1]:"—")+'</td></tr>').join("");
});
</script></body></html>`;

const RT_PAGE = `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>珠峰实时源</title><style>
:root{--bg:#0e1013;--fg:#e8e6e1;--mute:#8d8b86;--line:#2a2d33;--ok:#63c99a;--w:#e2b44c;--bad:#ef8a7e;--acc:#8fc3ff}
body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.5 system-ui,-apple-system,"PingFang SC","Noto Sans CJK SC",sans-serif}
main{max-width:1060px;margin:0 auto;padding:16px}h1{font-size:18px;margin:0 0 2px}h2{font-size:15px;margin:22px 0 6px}.sub{color:var(--mute);font-size:12px}
.g{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:10px}.c{background:#15181d;border-radius:8px;padding:10px}
.c img{width:100%;border-radius:6px;display:block;background:#222}table{width:100%;border-collapse:collapse;font-size:12px}td,th{padding:3px 4px;border-bottom:1px solid var(--line);text-align:left}
.k{display:inline-block;font-size:11px;padding:0 7px;border-radius:999px}.ok{background:rgba(99,201,154,.16);color:var(--ok)}.w{background:rgba(226,180,76,.16);color:var(--w)}.bad{background:rgba(239,138,126,.16);color:var(--bad)}
a{color:var(--acc)}svg{width:100%;height:60px}
</style></head><body><main><h1>珠峰实时源总览</h1><div class="sub" id="m">加载中…</div>
<h2>卫星云图（每 10–15 分钟）</h2><div class="g" id="img"></div>
<h2>地震（EMSC 实时 · 尼泊尔国家地震中心）</h2><div class="g"><div class="c"><b>EMSC · 珠峰 330 km 内，近 30 天</b><table id="emsc"></table></div><div class="c"><b>尼泊尔国家地震中心 · 最新</b><table id="nsc"></table></div></div>
<h2>当地网络连通（IODA · 萨加玛塔区）</h2><div class="c" id="ioda"></div>
<h2>空中交通（ADS-B · 卢卡拉周围 40 海里）</h2><div class="c" id="adsb"></div>
<h2>灾害警报（GDACS · 尼泊尔及珠峰附近）</h2><div class="c"><table id="gdacs"></table></div>
<h2>DORIS 信标 EVEC（Pyramid）· 卫星跟踪记录</h2><div class="c" id="doris"></div>
<p class="sub">只监测：显示各公开源的最新数据和时间，不判断、不预测。来源：NASA GIBS（向日葵 9 号）、EUMETSAT EUMETView（Meteosat IODC）、EMSC、尼泊尔国家地震中心、IODA（佐治亚理工）、ADS-B（adsb.lol / <a href=\"https://adsb.fi\">adsb.fi</a> / airplanes.live / OpenSky Network，非商业使用）、GDACS、IGN/IDS DORIS。<a href="/">← 冰坡雷达亮度</a></p></main>
<script>
const BJ=t=>t?new Date(t).toLocaleString("zh-CN",{timeZone:"Asia/Shanghai",hour12:false,month:"2-digit",day:"2-digit",hour:"2-digit",minute:"2-digit"}):"—";
const ago=t=>{if(!t)return"—";const m=(Date.now()-new Date(t))/6e4;return m<90?Math.round(m)+" 分钟前":m<2880?(m/60).toFixed(1)+" 小时前":Math.round(m/1440)+" 天前"};
const chip=(t,lim)=>{if(!t)return'<span class="k bad">无数据</span>';const m=(Date.now()-new Date(t))/6e4;return m<=lim?'<span class="k ok">实时</span>':m<=lim*6?'<span class="k w">延迟</span>':'<span class="k bad">停更</span>'};
const spark=(v,col)=>{v=(v||[]).filter(x=>x!=null);if(v.length<2)return"";const mn=Math.min(...v),mx=Math.max(...v),r=mx-mn||1;return'<svg viewBox="0 0 300 60" preserveAspectRatio="none"><polyline fill="none" stroke="'+col+'" stroke-width="1.5" points="'+v.map((y,i)=>(i/(v.length-1)*300).toFixed(1)+","+(55-(y-mn)/r*50).toFixed(1)).join(" ")+'"/></svg>'};
const IMGS=${JSON.stringify(IMG)};
const bad=s=>s&&s.ok===false?'<span class="k bad">取数失败</span> <span class="sub">'+(s.err||"")+'（'+BJ(s.at)+'）</span> ':"";
fetch("/api/rt.json").then(r=>r.json()).then(d=>{const S=d.sources||{};document.getElementById("m").textContent="汇总于 "+BJ(d.updated)+"（北京）。每 5 分钟一轮，各源按自己的节奏更新。";
 const g=(S.gibs||{}).v||{};document.getElementById("img").innerHTML=[["向日葵 9 号 可见光",IMGS.himawari_vis,g.vis_latest,30],["向日葵 9 号 红外（夜间也可见）",IMGS.himawari_ir,g.ir_latest,30],["Meteosat 雪 RGB（雪为红色调）",IMGS.meteosat_snow,null,0],["Meteosat 自然色增强",IMGS.meteosat_natural,null,0]].map(a=>'<div class="c"><b>'+a[0]+'</b> '+(a[2]?chip(a[2],a[3])+'<div class="sub">最新 '+BJ(a[2])+'（'+ago(a[2])+'）</div>':'<div class="sub">'+(a[3]?bad(S.gibs)||"最新一张":"EUMETView 最新一张")+'</div>')+'<img loading="lazy" src="'+a[1]+'" alt="'+a[0]+'"></div>').join("");
 const e=((S.emsc||{}).v||{}).events||[];document.getElementById("emsc").innerHTML=bad(S.emsc)+'<tr><th>时间（北京）</th><th>震级</th><th>地区</th></tr>'+e.slice(0,12).map(x=>'<tr><td>'+BJ(x.t)+'</td><td>'+x.mt+" "+x.mag+'</td><td>'+x.region+'</td></tr>').join("");
 const n=((S.nsc||{}).v||{}).events||[];document.getElementById("nsc").innerHTML=bad(S.nsc)+'<tr><th>时间（北京）</th><th>震级</th><th>地点</th></tr>'+n.slice(0,12).map(x=>'<tr><td>'+BJ(x.t)+'</td><td>'+x.mt+" "+x.mag+'</td><td>'+x.place+'</td></tr>').join("");
 const io=(S.ioda||{}).v||{};document.getElementById("ioda").innerHTML=bad(S.ioda)+chip(io.until,30)+' BGP 可达网段 <b>'+(io.bgp_last??"—")+'</b> · 主动探测有响应的地址块 <b>'+(io.ping_last??"—")+'</b><div class="sub">过去 24 小时（BGP）</div>'+spark((io.bgp||{}).v,"#8fc3ff")+'<div class="sub">过去 24 小时（主动探测）</div>'+spark((io.ping||{}).v,"#63c99a")+'<div class="sub">骤降可能是断网、断电或灾害，也可能是探测本身波动；本页不判断。</div>';
 const a=(S.adsb||{}).v||{};document.getElementById("adsb").innerHTML=(bad(S.adsb)||chip((S.adsb||{}).at,15))+' 当前 <b>'+(a.count??"—")+'</b> 架'+(a.source?' <span class="sub">（来源 '+a.source+'）</span>':'')+'<div class="sub">过去 24 小时架次（每 5 分钟）</div>'+spark((a.hist||[]).map(h=>h[1]),"#e2b44c")+'<table><tr><th>航班</th><th>机型</th><th>高度 ft</th><th>位置</th></tr>'+(a.now||[]).map(x=>'<tr><td>'+(x.flight||x.hex)+'</td><td>'+(x.type||"—")+'</td><td>'+(x.alt??"—")+'</td><td>'+(x.lat?x.lat.toFixed(3)+", "+x.lon.toFixed(3):"—")+'</td></tr>').join("")+'</table><div class="sub">不是所有直升机都装 ADS-B 发射器，没看到不代表没有飞行。</div>';
 const gd=((S.gdacs||{}).v||{}).events||[];document.getElementById("gdacs").innerHTML=bad(S.gdacs)+'<tr><th>开始</th><th>类型</th><th>级别</th><th>名称</th></tr>'+gd.map(x=>'<tr><td>'+BJ(x.from)+'</td><td>'+x.type+'</td><td>'+x.level+'</td><td>'+(x.url?'<a href="'+x.url+'" target="_blank" rel="noopener">'+x.name+'</a>':x.name)+'</td></tr>').join("");
 const dd=(S.doris||{}).v||{};const lp=dd.last_pass;document.getElementById("doris").innerHTML=bad(S.doris)+(lp?chip(lp.last,6*60)+' 最近一次被跟踪 <b>'+BJ(lp.last)+'</b>（'+ago(lp.last)+'，卫星 '+lp.sat+'，'+lp.n+' 条观测）':'<span class="k w">首次运行，正在逐颗卫星检查</span>')+' · 过去 24 小时被跟踪 <b>'+(dd.passes_24h??"—")+'</b> 次<table><tr><th>卫星</th><th>开始</th><th>结束</th><th>观测数</th></tr>'+(dd.passes||[]).slice(-10).reverse().map(p=>'<tr><td>'+p.sat+'</td><td>'+BJ(p.first)+'</td><td>'+BJ(p.last)+'</td><td>'+p.n+'</td></tr>').join("")+'</table><div class="sub">数据来自 IGN 匿名 FTP 的准实时文件（延迟 2–3 小时），每 30 分钟查一颗卫星，轮流检查 9 颗。只说明信标在工作，不是位置变化。</div>';
});
</script></body></html>`;
