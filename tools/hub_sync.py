"""每小时把实时采集结果整理成总览页数据库要的文档（JSON 文件），由定时任务用 ArtifactData 写入。
用法：python3 tools/hub_sync.py <输出目录>
输出：live_<名>.json → 数据库 live/<名>（rt 实时采集、fs 坡面+事件+灾种、img 卫星图、cam 摄像头、hzr 全部灾种记录、lib 外部工具库、ops 自动流程运行记录），
      mt_monitor.json → mt_monitor/latest"""
import base64, json, os, subprocess, sys, time
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
REPO = "Yizebaba/EVEREST-"
def raw(path, ref="facet-live"):
    # 仓库是公开的：先走 raw.githubusercontent.com（不需要任何仓库权限；10-16 起定时任务会话的 gh 对本仓库返回 403），失败再用 gh
    import urllib.request, urllib.parse
    try:
        u = f"https://raw.githubusercontent.com/{REPO}/{ref}/" + urllib.parse.quote(path)
        with urllib.request.urlopen(urllib.request.Request(u, headers={"user-agent": "everest-hub-sync"}), timeout=60) as r: return r.read()
    except Exception:
        return subprocess.check_output(["gh", "api", "-H", "Accept: application/vnd.github.raw", f"repos/{REPO}/contents/{path}?ref={ref}"], stderr=subprocess.DEVNULL)
rt = json.loads(raw("rt.json")); fs = json.loads(raw("facet_status.json"))
json.dump(rt, open(f"{out}/live_rt.json", "w"), ensure_ascii=False)
json.dump(fs, open(f"{out}/live_fs.json", "w"), ensure_ascii=False)
img = {"at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
# 卫星图（Worker 每 30 分钟存一份 JPEG；旧的 PNG 作后备）。单个文档上限 256 KiB，超了按顺序少放几张
for k in ("himawari_vis", "himawari_ir", "himawari_am", "meteosat_natural", "meteosat_snow"):
    for ext, mime in (("jpg", "image/jpeg"), ("png", "image/png")):
        try:
            b = raw(f"img/{k}.{ext}")
            # 一张图几乎全是同一种颜色（夜间的可见光 / 自然色，或来源暂缺时的空白图）：JPEG 只有一两 KB。标出来，页面不显示空图
            if ext == "jpg" and len(b) < 3000: img.setdefault("blank", []).append(k)
            img[k] = f"data:{mime};base64," + base64.b64encode(b).decode(); break
        except Exception as e: pass
    if k not in img: print("图像暂缺", k)
# 珠峰地区摄像头（hazards 工作流每小时检查，tools/webcams.py）：是否在播、源地址、一张小图
try:
    wc = json.loads(raw("hazards/webcams.json", "events")); cams = []
    for c in wc.get("cams", []):
        x = {k: c.get(k) for k in ("id", "kind", "title", "operator", "url", "channel", "live", "last_image", "fetched", "note")}
        if c.get("file") and (c.get("bytes") or 0) <= 60000:
            try: x["img"] = "data:image/jpeg;base64," + base64.b64encode(raw(c["file"], "events")).decode()
            except Exception as e: print("cam img", c["id"], e)
        cams.append(x)
    json.dump({"updated": wc.get("updated"), "list": cams}, open(f"{out}/live_cam.json", "w"))   # 摄像头单独一个文档（→ live/cam）
    img["cams"] = {"updated": wc.get("updated"), "list": cams}   # 旧版页面从 live/img 读摄像头；放得下就也放一份
except Exception as e:
    print("webcams", e)
if len(json.dumps(img).encode()) > 235000: img.pop("cams", None)
for k in ("meteosat_snow", "himawari_vis", "meteosat_natural", "himawari_ir"):
    if len(json.dumps(img).encode()) <= 235000: break
    img.pop(k, None); print("图像太大，去掉", k)
json.dump(img, open(f"{out}/live_img.json", "w"))
sys.path.insert(0, os.path.dirname(__file__))
from monitor_sync import build
json.dump(build(rt), open(f"{out}/mt_monitor.json", "w"), ensure_ascii=False)
for f in ("live_rt", "live_fs", "live_img", "live_cam", "mt_monitor"):
    if os.path.exists(f"{out}/{f}.json"): print(f, os.path.getsize(f"{out}/{f}.json"), "bytes")
print("rt.updated", rt.get("updated"), "facet", fs.get("scenes"))

# 事件与证据包（events 分支，由 evidence 工作流生成）→ live_ev.json（→ live/ev）
try:
    idx = json.loads(raw("index.json", "events")).get("events", {})
    evs = []
    for eid, m in sorted(idx.items(), key=lambda kv: (kv[1].get("first_seen") or kv[1]["t"], kv[0])):
        if time.time() - time.mktime(time.strptime(m["t"][:19], "%Y-%m-%dT%H:%M:%S")) > 60 * 86400: continue
        try: p = json.loads(raw(f"events/{eid}.json", "events"))
        except Exception: continue
        e = {k: p.get(k) for k in ("id", "hips", "title", "title_en", "kind", "place", "lat", "lon", "t", "built", "note", "note_en")}
        e["first_seen"] = m.get("first_seen"); e["timeline"] = p.get("timeline", [])[:60]
        # 最新一条记录的时间（在完整时间线上算，时间线后面会被截短）
        ts = [x["t"] for x in p.get("timeline", []) if x.get("kind") in ("SUPPORTING", "CONTRADICTORY") and x.get("t") and x["t"] <= (p.get("built") or "9")]
        e["last_t"] = max(ts + [p.get("t") or ""]) or None
        e["evn"] = {k: (p.get("evn") or {}).get(k) for k in ("distance_km", "coverage_pct", "peaks", "error")}
        e["sentinel"] = p.get("sentinel"); e["gauges"] = p.get("gauges"); e["ioda"] = p.get("ioda")
        e["kkn"] = p.get("kkn"); e["gfm"] = p.get("gfm"); e["ots"] = m.get("ots", [])[-3:]; e["manual"] = p.get("manual")
        e["receipts_n"] = len(p.get("receipts") or [])
        e["bounds"] = p.get("bounds")   # 推断边界：每类来源能说明什么、不能说明什么
        h = p.get("history")   # 冰湖溃决数据库：事件 30 km 内的历史记录（带数据库版本），只作背景
        if h: e["history"] = {"n": h.get("n"), "radius_km": h.get("radius_km"), "records": (h.get("records") or [])[:8],
                              "source": {k: (h.get("source") or {}).get(k) for k in ("name", "file", "commit", "commit_time", "release_doi", "paper")}}
        if p.get("references"): e["references"] = [{"hips": r.get("hips"), "hazard": r.get("hazard"), "data_papers": (r.get("data_papers") or [])[:3],
                                                   "venues": [v.get("name") for v in (r.get("venues") or [])][:3]} for r in p["references"][:2]]
        png = p.get("png") or (p.get("evn") or {}).get("png")
        if png and time.time() - time.mktime(time.strptime(m["t"][:19], "%Y-%m-%dT%H:%M:%S")) < 21 * 86400:
            try: e["evn_png"] = "data:image/png;base64," + base64.b64encode(raw(f"events/{png}", "events")).decode()
            except Exception as x: print("图", eid, x)
        evs.append(e)
    # 281 种灾害的实测扫描结果（hazards 工作流每小时更新）：精简后放进 live_fs 的 hz 字段
    try:
        sc = json.loads(raw("hazards/scan.json", "events"))
        fs["hz"] = {"updated": sc["updated"], "by_latency": sc.get("by_latency"),
                    "src": {k: [v.get("state"), v.get("n"), v.get("local"), (v.get("err") or v.get("need") or "")[:60], v.get("latency")] for k, v in sc["sources"].items()},
                    "h": [[h["code"], h["state"], h["n_local_90d"], h["n_90d"], h["latest"], (h["latest_title"] or "")[:90], h.get("latest_url"), len(h["tested_ok"]), h.get("rt_tier")] for h in sc["hazards"]]}
    except Exception as x:
        print("灾种扫描结果暂缺：", x)
    # 数据库单个文档上限 256 KiB：只给最近 3 个事件带图，超了就从最早的开始去掉图
    for e in sorted(evs, key=lambda e: e["t"])[:-3]: e.pop("evn_png", None)
    mi = json.loads(raw("index.json", "events")).get("manual") or {}
    evd = {"updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "events": evs, "manual_ots": (mi.get("ots") or [])[-3:]}
    for e in sorted(evs, key=lambda e: e["t"]):
        if len(json.dumps({**fs, "ev": evd}, ensure_ascii=False).encode()) < 230000: break
        e.pop("evn_png", None)
    size = lambda: len(json.dumps({**fs, "ev": evd}, ensure_ascii=False).encode())
    for cap in (40, 25, 12):   # 还超就从最早的事件开始缩短时间线（完整时间线在连接器和 events 分支里）
        for e in sorted(evs, key=lambda e: e["t"]):
            if size() < 230000: break
            e["timeline"] = e["timeline"][:cap]; e.pop("news", None)
    if size() >= 250000: print("警告：live_fs 仍然过大", size())
    json.dump(evd, open(f"{out}/live_ev.json", "w"), ensure_ascii=False)
    # 同时并进 live_fs.json 的 ev 字段：定时任务原本就写 live/fs，不用改任务也能把事件送到页面
    fs["ev"] = evd
    json.dump(fs, open(f"{out}/live_fs.json", "w"), ensure_ascii=False)
    print("live_ev", os.path.getsize(f"{out}/live_ev.json"), "bytes,", len(evs), "events；live_fs", os.path.getsize(f"{out}/live_fs.json"), "bytes")
except Exception as e:
    print("事件证据包暂缺：", e)

DOCK_EXCL = {  # 与 cf-worker/src/hub.js、页面 DOCK_EXCL 保持一致
    "机场天气实况 METAR", "航空危险天气通报 SIGMET", "美国风暴实况报告 SPC", "美国气象局已观测警报 NWS", "NOAA SWPC 空间天气",   # 天气类观测与通报
    "CelesTrak 在轨目标", "IOC 海平面站", "OpenPhish 钓鱼列表", "abuse.ch ThreatFox", "美国林火实时 NIFC", "GBIF 物种记录（尼泊尔）",
    "NSIDC 海冰", "BIPAD 空气质量站", "WHO FluNet（尼泊尔）", "Sentinel-5P 大气成分", "ADS-B 紧急代码 7700"}   # 每次扫描重复的状态计数或观测读数
# 全部灾种扫描记录（不只珠峰）：最近 30 天、按时间倒序，精简后写 live_hzr.json（→ live/hzr），底部事件栏“全部记录”用。
try:
    rec = json.loads(raw("hazards/records.json", "events"))
    # v80：底部事件栏只放“事件”：去掉常规天气观测流（平台不做天气）、每次扫描都重复的状态计数、标为观测的记录；同来源同标题只留最新一条
    R = [r for r in rec.get("records", []) if r.get("t") and not r.get("observation") and r.get("src") not in DOCK_EXCL]
    seen = set(); R2 = []
    for r in sorted(R, key=lambda r: r["t"], reverse=True):
        k = (r.get("src"), r.get("title")); 
        if k in seen: continue
        seen.add(k); R2.append(r)
    R = R2
    cut = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() - 30 * 86400))
    R = sorted([r for r in R if r["t"] >= cut], key=lambda r: r["t"], reverse=True)
    def row(r):
        x = [r["t"], (r.get("title") or "")[:140], r.get("src") or "", r.get("url") or "", r.get("lat"), r.get("lon"), (r.get("codes") or [])[:3], 1 if r.get("local") else 0]
        if "deaths" in r: x.append([r.get("deaths"), r.get("injured"), r.get("missing")])
        return x
    rows = []; size = 200
    for r in [r for r in R if r.get("local")] + [r for r in R if not r.get("local")]:   # 先放尼泊尔 / 珠峰范围，再按时间放全球，预算用完为止
        x = row(r); n = len(json.dumps(x, ensure_ascii=False).encode()) + 1
        if size + n > 225000: continue
        size += n; rows.append(x)
    rows.sort(key=lambda x: x[0], reverse=True)
    json.dump({"updated": rec.get("updated"), "total": len(R), "n": len(rows), "r": rows}, open(f"{out}/live_hzr.json", "w"), ensure_ascii=False)
    print("live_hzr", os.path.getsize(f"{out}/live_hzr.json"), "bytes,", len(rows), "/", len(R), "records")
except Exception as e:
    print("灾种扫描记录暂缺：", e)

# 外部工具库目录（tools/catalog.py，随灾种扫描每小时更新）→ live_lib.json（→ live/lib）
try:
    cat = json.loads(raw("hazards/catalog.json", "events"))
    lib = {"updated": cat.get("updated"),
           "skills": [{k: s.get(k) for k in ("name", "desc", "url", "raw", "src", "license")} for s in cat.get("skills", [])],
           "plugins": [{k: p.get(k) for k in ("name", "desc", "cat", "src", "repo", "url", "install")} for p in cat.get("plugins", [])],
           "mcp": [{k: m.get(k) for k in ("name", "title", "desc", "version", "repo", "remote", "pkg", "site")} for m in cat.get("mcp", [])]}
    while len(json.dumps(lib, ensure_ascii=False).encode()) > 225000 and lib["mcp"]: lib["mcp"] = lib["mcp"][:int(len(lib["mcp"]) * .8)]
    json.dump(lib, open(f"{out}/live_lib.json", "w"), ensure_ascii=False)
    print("live_lib", os.path.getsize(f"{out}/live_lib.json"), "bytes;", len(lib["skills"]), "skills", len(lib["plugins"]), "plugins", len(lib["mcp"]), "mcp")
except Exception as e:
    print("外部工具库目录暂缺：", e)

# 自动流程审计：GitHub Actions 最近 60 次运行（名称、分支、触发方式、结果、时间、链接）→ live_ops.json（→ live/ops）
try:
    rr = json.loads(subprocess.check_output(["gh", "api", f"repos/{REPO}/actions/runs?per_page=60"], stderr=subprocess.DEVNULL))
    ops = [[r.get("name"), r.get("head_branch"), r.get("event"), r.get("status"), r.get("conclusion"), r.get("created_at"), r.get("updated_at"), r.get("html_url"), r.get("run_number")]
           for r in rr.get("workflow_runs", [])]
    json.dump({"updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "runs": ops}, open(f"{out}/live_ops.json", "w"), ensure_ascii=False)
    print("live_ops", len(ops), "runs")
except Exception as e:
    # 没有 gh 权限的环境（定时任务会话）：用 hazards 工作流每次扫描后写的 events 分支 hub/ops.json（已含运行记录、InSAR、卫星过境、MiroFish）
    try:
        json.dump(json.loads(raw("hub/ops.json", "events")), open(f"{out}/live_ops.json", "w"), ensure_ascii=False); print("live_ops 取自 events hub/ops.json（本环境没有 gh 权限）")
    except Exception as e2:
        print("运行记录暂缺：", e, e2)

# 仓库每日 InSAR 管线的最新产物和自动核对（读 main 分支 data/displacement_summary.json），并进 live_ops.json 的 pipe 字段
try:
    from datetime import date
    sm = json.loads(raw("data/displacement_summary.json", "main"))
    ins = (sm.get("results") or {}).get("insar_displacement") or {}
    pair = sm.get("insar_pair") or {}; cp = ins.get("cloud_pair") or {}
    try: gap = (date.fromisoformat(pair["slave"]) - date.fromisoformat(pair["master"])).days
    except Exception: gap = None
    checks = [
        {"ok": str(ins.get("source", "")).startswith("cloud_insar"), "t": "位移只认云端干涉（哥白尼 openEO）的真实结果；没有结果或没有参考点就不给毫米数（不再用仓库里的固定矩阵）" if str(ins.get("source", "")).startswith("cloud_insar") else "位移数值不是来自云端干涉真实结果"},
        {"ok": gap == 12, "t": f"影像对 {pair.get('master')} → {pair.get('slave')} 相隔 {gap} 天" + ("，是同一条带（23790，相对轨道 12）的 12 天重访" if gap == 12 else "，不是同一条带的 12 天重访，不能做干涉")},
        {"ok": bool(cp) and str(cp.get("slave", "")) >= str(pair.get("slave", "")), "t": f"云端干涉最新 {cp.get('master')} → {cp.get('slave')}" + ("，已覆盖最新影像对" if cp and str(cp.get('slave', '')) >= str(pair.get('slave', '')) else "，还没算到最新影像对")},
    ]
    cm = json.loads(subprocess.check_output(["gh", "api", f"repos/{REPO}/commits?path=data/displacement_summary.json&per_page=3"], stderr=subprocess.DEVNULL))
    pipe = {"generated": (sm.get("timestamp_utc") or "")[:19], "pair": pair, "burst": sm.get("burst_id"),
            "insar": {k: ins.get(k) for k in ("status", "reason", "median_mm", "max_mm", "evaluated_candidate_pixels", "valid_phase_pixels", "coherence_mean", "cloud_pair", "displacement_status", "cloud_processed_utc")},
            "auto": {"t": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "checks": checks},
            "commits": [{"t": c["commit"]["committer"]["date"], "sha": c["sha"][:7]} for c in cm]}
    opsf = f"{out}/live_ops.json"
    o = json.load(open(opsf)) if os.path.exists(opsf) else {"updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "runs": []}
    o["pipe"] = pipe
    try: o["sat"] = json.loads(raw("hazards/sat.json", "events"))   # 哨兵卫星过境目录（hazards 工作流每小时）
    except Exception as e: print("卫星目录暂缺：", e)
    # MiroFish 推演（不是证据）：最近一次运行的状态、输入文件、报告前 60 KB
    try:
        L = raw("mirofish/LATEST", "events").decode().strip()
        mf = {"dir": L}
        for f in ("status.json", "secrets_check.json", "input/manifest.json"):
            try: mf[f.split("/")[-1].replace(".json", "")] = json.loads(raw(f"{L}/{f}", "events"))
            except Exception: pass
        try: mf["requirement"] = raw(f"{L}/input/requirement.txt", "events").decode()[:3000]
        except Exception: pass
        try: mf["report"] = raw(f"{L}/REPORT.md", "events").decode()[:60000]
        except Exception: pass
        o["mf"] = mf
    except Exception as e: print("MiroFish 暂无：", e)
    json.dump(o, open(opsf, "w"), ensure_ascii=False)
    print("pipe", pipe["pair"], [c["ok"] for c in checks])
except Exception as e:
    print("管线产物暂缺：", e)

# 281 种灾害的文献与数据源（venues.json：OpenAlex + Crossref；scan.json：每种灾害能用的公开来源）→ live_lit.json（→ live/lit）
try:
    ven = json.loads(raw("hazards/venues.json", "events")); sc2 = json.loads(raw("hazards/scan.json", "events"))
    srcmap = {h["code"]: [h.get("sources") or [], h.get("tested_ok") or []] for h in sc2.get("hazards", [])}
    def cut(s, n): s = s or ""; return s if len(s) <= n else s[:n - 1] + "…"
    def build(nv, npp, tl):
        L = []
        for h in ven.get("hazards", []):
            vv = (h.get("top_venues") or h.get("most_active") or [])[:nv]
            L.append({"c": h["code"], "q": h.get("query"), "n": h.get("papers_2020"),
                      "v": [[x.get("name"), x.get("h"), x.get("url"), 1 if x.get("oa") else 0] for x in vv],
                      "m": [x.get("name") for x in (h.get("multidisciplinary") or [])[:2]],
                      "d": [[cut(x.get("title"), tl), x.get("doi"), x.get("year"), x.get("journal")] for x in (h.get("data_papers") or [])[:npp]],
                      "p": [[cut(x.get("title"), tl), x.get("doi"), x.get("year"), x.get("cites"), x.get("journal") or x.get("venue")] for x in (h.get("top_papers") or [])[:npp]],
                      "s": srcmap.get(h["code"], [[], []])})
        return L
    for nv, npp, tl in ((5, 3, 140), (4, 3, 110), (3, 2, 100), (3, 2, 80), (2, 1, 80)):
        lit = {"generated": ven.get("generated"), "method": ven.get("method"), "done": ven.get("done"), "total": ven.get("total"), "h": build(nv, npp, tl)}
        if len(json.dumps(lit, ensure_ascii=False).encode()) < 235000: break
    json.dump(lit, open(f"{out}/live_lit.json", "w"), ensure_ascii=False)
    print("live_lit", os.path.getsize(f"{out}/live_lit.json"), "bytes;", len(lit["h"]), "hazards")
except Exception as e:
    print("文献表暂缺：", e)
