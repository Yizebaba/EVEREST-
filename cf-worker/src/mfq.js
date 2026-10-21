// MiroFish 推演排队（谁推演谁用自己的密钥）。
// 网页 POST /mf/submit：推演要求 + 使用者自己的模型密钥和 Zep 密钥 → 先试一下密钥 → 存进 D1 排队。
// GitHub Actions（本仓库 mirofish-queue.yml / mirofish.yml）用 GitHub OIDC 身份领取任务：/mf/take 取编号，/mf/claim 取密钥（取走即从库里删除），/mf/done 回报结果。
// 使用者可另外上传 PDF/Markdown/TXT（最多 5 个，单个 10 MB，合计 20 MB），分块存 D1 表 mf_files，推演工作流取走即删除。
// 密钥只在排队期间存放，领取后立刻删除；超过 6 小时没被领取也删除。公开接口 /mf/job 只返回状态，不含密钥。
const REPO = "Yizebaba/EVEREST-";
const WF = REPO + "/.github/workflows/";
const AUD = "everest-mf";
const MAX_QUEUED = 20, MAX_PER_IP_DAY = 4, MAX_RUNNING = 3;
const H = { "content-type": "application/json; charset=utf-8", "access-control-allow-origin": "*", "access-control-allow-headers": "content-type, authorization", "access-control-allow-methods": "GET, POST, OPTIONS", "cache-control": "no-store" };
const J = (o, s = 200) => new Response(JSON.stringify(o), { status: s, headers: H });
const now = () => new Date().toISOString();
const SCHEMA = [`CREATE TABLE IF NOT EXISTS mf_jobs (id TEXT PRIMARY KEY, created TEXT, state TEXT, project TEXT, scope TEXT, title TEXT, requirement TEXT, rounds INTEGER,
  secret TEXT, iph TEXT, dispatched TEXT, claimed TEXT, finished TEXT, run_url TEXT, dir TEXT, ok INTEGER, error TEXT)`,
  `CREATE TABLE IF NOT EXISTS mf_files (job TEXT, name TEXT, idx INTEGER, data TEXT, PRIMARY KEY (job, name, idx))`];
const MAX_FILES = 5, MAX_FILE = 10 * 1024 * 1024, MAX_TOTAL = 20 * 1024 * 1024, CHUNK = 900000, EXT = /\.(pdf|md|markdown|txt)$/i;

async function init(env) { for (const s of SCHEMA) await env.DB.prepare(s).run(); }
async function sha(s) { const b = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s)); return [...new Uint8Array(b)].map(x => x.toString(16).padStart(2, "0")).join(""); }
const pub = r => r && ({ id: r.id, state: r.state, project: r.project, scope: r.scope, title: r.title, created: r.created, dispatched: r.dispatched, claimed: r.claimed, finished: r.finished, run_url: r.run_url, dir: r.dir, ok: r.ok, error: r.error });

async function sweep(env) {   // 过期清理：6 小时没人领的删密钥并标失败；派出 60 分钟还没领取的回到排队
  const t6 = new Date(Date.now() - 6 * 3600e3).toISOString(), t1 = new Date(Date.now() - 3600e3).toISOString();
  await env.DB.prepare("UPDATE mf_jobs SET secret=NULL, state='expired' WHERE state IN ('queued','dispatched') AND created < ?").bind(t6).run();
  await env.DB.prepare("DELETE FROM mf_files WHERE job IN (SELECT id FROM mf_jobs WHERE state IN ('expired','done','failed') OR created < ?)").bind(new Date(Date.now() - 24 * 3600e3).toISOString()).run();
  await env.DB.prepare("UPDATE mf_jobs SET state='queued', dispatched=NULL WHERE state='dispatched' AND dispatched < ?").bind(t1).run();
}

async function testLLM(base, model, key) {
  try {
    const r = await fetch(base.replace(/\/+$/, "") + "/chat/completions", { method: "POST", headers: { "content-type": "application/json", authorization: "Bearer " + key },
      body: JSON.stringify({ model, messages: [{ role: "user", content: "ok" }], max_tokens: 1 }) });
    if (r.ok) return null;
    const t = (await r.text()).slice(0, 200);
    return { 401: "模型密钥无效", 402: "模型账户余额不足", 403: "模型密钥没有权限", 404: "接口地址或模型名不对", 429: "模型接口限流，稍后再试" }[r.status] || ("模型接口返回 " + r.status + "：" + t);
  } catch (e) { return "连不上模型接口：" + String(e).slice(0, 120); }
}
async function testZep(key) {
  try {
    const r = await fetch("https://api.getzep.com/api/v2/users-ordered?pageNumber=1&pageSize=1", { headers: { authorization: "Api-Key " + key } });
    return r.status === 401 || r.status === 403 ? "Zep 密钥无效" : null;
  } catch (e) { return null; }
}

// GitHub Actions OIDC 令牌验证（RS256，公钥取自 GitHub）
let JWKS = null;
async function oidc(req) {
  const tok = (req.headers.get("authorization") || "").replace(/^Bearer\s+/i, "");
  const p = tok.split("."); if (p.length !== 3) throw new Error("no token");
  const dec = s => Uint8Array.from(atob(s.replace(/-/g, "+").replace(/_/g, "/") + "===".slice((s.length + 3) % 4)), c => c.charCodeAt(0));
  const hd = JSON.parse(new TextDecoder().decode(dec(p[0]))), cl = JSON.parse(new TextDecoder().decode(dec(p[1])));
  if (!JWKS || !JWKS.keys.some(k => k.kid === hd.kid)) JWKS = await (await fetch("https://token.actions.githubusercontent.com/.well-known/jwks")).json();
  const jwk = JWKS.keys.find(k => k.kid === hd.kid); if (!jwk) throw new Error("unknown key");
  const key = await crypto.subtle.importKey("jwk", jwk, { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" }, false, ["verify"]);
  if (!(await crypto.subtle.verify("RSASSA-PKCS1-v1_5", key, dec(p[2]), new TextEncoder().encode(p[0] + "." + p[1])))) throw new Error("bad signature");
  const t = Date.now() / 1000;
  if (cl.iss !== "https://token.actions.githubusercontent.com" || cl.aud !== AUD || cl.exp < t || cl.nbf > t + 60) throw new Error("bad claims");
  if (cl.repository !== REPO || !String(cl.workflow_ref || "").startsWith(WF)) throw new Error("wrong repo/workflow");
  return cl;
}

export async function handleMf(req, env, u) {
  if (req.method === "OPTIONS") return new Response(null, { headers: H });
  await init(env);
  const p = u.pathname;
  if (p === "/mf/job") {
    const ids = (u.searchParams.get("id") || "").split(",").filter(x => /^[a-z0-9]{6,32}$/.test(x)).slice(0, 20);
    const out = {};
    for (const id of ids) out[id] = pub(await env.DB.prepare("SELECT * FROM mf_jobs WHERE id=?").bind(id).first());
    const q = await env.DB.prepare("SELECT COUNT(*) n FROM mf_jobs WHERE state IN ('queued','dispatched')").first();
    const r = await env.DB.prepare("SELECT COUNT(*) n FROM mf_jobs WHERE state='running'").first();
    return J({ jobs: out, queued: q.n, running: r.n });
  }
  if (p === "/mf/submit" && req.method === "POST") {
    await sweep(env);
    let b; try { b = await req.json(); } catch (e) { return J({ error: "格式不对" }, 400); }
    const s = x => String(x || "").trim();
    const reqm = s(b.requirement), scope = s(b.scope).toUpperCase().replace(/[^A-Z,]/g, ""), title = s(b.title).slice(0, 120);
    const llm = { key: s(b.llm_key), base: s(b.llm_base), model: s(b.llm_model) }, zep = s(b.zep_key);
    const rounds = parseInt(b.rounds) > 0 ? Math.max(5, Math.min(200, parseInt(b.rounds))) : 0, project = b.project === "everest" ? "everest" : "bri";
    if (reqm.length < 10 || reqm.length > 4000) return J({ error: "推演要求要自己写，10 到 4000 字" }, 400);
    if (project === "bri" && !scope) return J({ error: "请选国家" }, 400);
    if (!llm.key || !/^https:\/\//.test(llm.base) || !llm.model) return J({ error: "请填模型接口地址、模型名和密钥" }, 400);
    if (!zep) return J({ error: "请填 Zep 密钥" }, 400);
    const iph = await sha((req.headers.get("cf-connecting-ip") || "") + now().slice(0, 10));
    const nip = (await env.DB.prepare("SELECT COUNT(*) n FROM mf_jobs WHERE iph=?").bind(iph).first()).n;
    if (nip >= MAX_PER_IP_DAY) return J({ error: "今天提交次数已满，明天再来" }, 429);
    const nq = (await env.DB.prepare("SELECT COUNT(*) n FROM mf_jobs WHERE state IN ('queued','dispatched')").first()).n;
    if (nq >= MAX_QUEUED) return J({ error: "排队的人太多，稍后再试" }, 429);
    const e1 = await testLLM(llm.base, llm.model, llm.key); if (e1) return J({ error: e1, field: "llm" }, 400);
    const e2 = await testZep(zep); if (e2) return J({ error: e2, field: "zep" }, 400);
    const files = Array.isArray(b.files) ? b.files : [];
    if (files.length > MAX_FILES) return J({ error: "最多上传 5 个文件" }, 400);
    let tot = 0;
    for (const f of files) {
      const sz = Math.floor(String(f.data || "").length * 3 / 4); tot += sz;
      if (!EXT.test(String(f.name || "")) || !f.data) return J({ error: "只支持 PDF、Markdown、TXT：" + String(f.name || "").slice(0, 60) }, 400);
      if (sz > MAX_FILE) return J({ error: "单个文件不能超过 10 MB：" + String(f.name).slice(0, 60) }, 400);
    }
    if (tot > MAX_TOTAL) return J({ error: "上传文件合计不能超过 20 MB" }, 400);
    const id = (Date.now().toString(36) + crypto.getRandomValues(new Uint32Array(1))[0].toString(36)).slice(0, 16);
    await env.DB.prepare("INSERT INTO mf_jobs (id,created,state,project,scope,title,requirement,rounds,secret,iph) VALUES (?,?,?,?,?,?,?,?,?,?)")
      .bind(id, now(), "queued", project, scope.split(",").filter(Boolean).slice(0, 5).join(","), title, reqm, rounds, JSON.stringify({ llm, zep }), iph).run();
    for (const f of files) {
      const nm = String(f.name).replace(/[\\/:*?"<>|\x00-\x1f]/g, "_").slice(-100), d = String(f.data);
      for (let i = 0, k = 0; i < d.length; i += CHUNK, k++) await env.DB.prepare("INSERT OR REPLACE INTO mf_files (job,name,idx,data) VALUES (?,?,?,?)").bind(id, nm, k, d.slice(i, i + CHUNK)).run();
    }
    return J({ id, state: "queued", files: files.length });
  }
  // 以下只给本仓库的 GitHub Actions（OIDC）
  let cl; try { cl = await oidc(req); } catch (e) { return J({ error: "forbidden: " + e.message }, 403); }
  if (p === "/mf/take" && req.method === "POST") {   // 排队工作流取要派出的任务编号（不含密钥）
    await sweep(env);
    const run = (await env.DB.prepare("SELECT COUNT(*) n FROM mf_jobs WHERE state IN ('dispatched','running')").first()).n;
    const rows = (await env.DB.prepare("SELECT id,project,scope,title,rounds FROM mf_jobs WHERE state='queued' ORDER BY created LIMIT ?").bind(Math.max(0, MAX_RUNNING - run)).all()).results || [];
    for (const r of rows) await env.DB.prepare("UPDATE mf_jobs SET state='dispatched', dispatched=? WHERE id=? AND state='queued'").bind(now(), r.id).run();
    return J({ jobs: rows });
  }
  if (p === "/mf/claim" && req.method === "POST") {   // 推演工作流领取：返回要求和密钥，同时从库里删掉密钥
    const b = await req.json().catch(() => ({}));
    const r = await env.DB.prepare("SELECT * FROM mf_jobs WHERE id=? AND state IN ('queued','dispatched') AND secret IS NOT NULL").bind(String(b.id || "")).first();
    if (!r) return J({ error: "no such job" }, 404);
    const run_url = `https://github.com/${REPO}/actions/runs/${cl.run_id}`;
    await env.DB.prepare("UPDATE mf_jobs SET state='running', secret=NULL, claimed=?, run_url=? WHERE id=?").bind(now(), run_url, r.id).run();
    const sc = JSON.parse(r.secret);
    const fl = ((await env.DB.prepare("SELECT DISTINCT name FROM mf_files WHERE job=?").bind(r.id).all()).results || []).map(x => x.name);
    return J({ files: fl, id: r.id, project: r.project, scope: r.scope, title: r.title, requirement: r.requirement, rounds: r.rounds, llm_key: sc.llm.key, llm_base: sc.llm.base, llm_model: sc.llm.model, zep_key: sc.zep });
  }
  if (p === "/mf/file" && req.method === "POST") {   // 推演工作流取使用者上传的文件（取走即删除）
    const b = await req.json().catch(() => ({}));
    const rows = ((await env.DB.prepare("SELECT data FROM mf_files WHERE job=? AND name=? ORDER BY idx").bind(String(b.id || ""), String(b.name || "")).all()).results || []);
    if (!rows.length) return J({ error: "no such file" }, 404);
    await env.DB.prepare("DELETE FROM mf_files WHERE job=? AND name=?").bind(String(b.id), String(b.name)).run();
    return J({ name: b.name, data: rows.map(x => x.data).join("") });
  }
  if (p === "/mf/done" && req.method === "POST") {
    const b = await req.json().catch(() => ({}));
    await env.DB.prepare("UPDATE mf_jobs SET state=?, finished=?, dir=?, ok=?, error=? WHERE id=?")
      .bind(b.ok ? "done" : "failed", now(), String(b.dir || "").slice(0, 120), b.ok ? 1 : 0, String(b.error || "").slice(0, 300), String(b.id || "")).run();
    return J({ ok: true });
  }
  return J({ error: "not found" }, 404);
}
