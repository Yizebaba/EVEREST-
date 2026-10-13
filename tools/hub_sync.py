"""每小时把实时采集结果整理成总览页数据库要的 4 个文档（JSON 文件），由定时任务用 ArtifactData 写入。
用法：python3 tools/hub_sync.py <输出目录>
输出：live_rt.json（→ live/rt）、live_fs.json（→ live/fs）、live_img.json（→ live/img）、mt_monitor.json（→ mt_monitor/latest）"""
import base64, json, os, subprocess, sys, time
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
REPO = "Yizebaba/everest-insar-pipeline"
def raw(path, ref="facet-live"):
    return subprocess.check_output(["gh", "api", "-H", "Accept: application/vnd.github.raw", f"repos/{REPO}/contents/{path}?ref={ref}"])
rt = json.loads(raw("rt.json")); fs = json.loads(raw("facet_status.json"))
json.dump(rt, open(f"{out}/live_rt.json", "w"), ensure_ascii=False)
json.dump(fs, open(f"{out}/live_fs.json", "w"), ensure_ascii=False)
img = {"at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
for k in ("himawari_vis", "meteosat_snow"):
    try: img[k] = "data:image/png;base64," + base64.b64encode(raw(f"img/{k}.png")).decode()
    except Exception as e: print("图像", k, e)
json.dump(img, open(f"{out}/live_img.json", "w"))
sys.path.insert(0, os.path.dirname(__file__))
from monitor_sync import build
json.dump(build(rt), open(f"{out}/mt_monitor.json", "w"), ensure_ascii=False)
for f in ("live_rt", "live_fs", "live_img", "mt_monitor"): print(f, os.path.getsize(f"{out}/{f}.json"), "bytes")
print("rt.updated", rt.get("updated"), "facet", fs.get("scenes"))

# 事件与证据包（events 分支，由 evidence 工作流生成）→ live_ev.json（→ live/ev）
try:
    idx = json.loads(raw("index.json", "events")).get("events", {})
    evs = []
    for eid, m in sorted(idx.items(), key=lambda kv: (kv[1].get("first_seen") or kv[1]["t"], kv[0])):
        if time.time() - time.mktime(time.strptime(m["t"][:19], "%Y-%m-%dT%H:%M:%S")) > 60 * 86400: continue
        try: p = json.loads(raw(f"events/{eid}.json", "events"))
        except Exception: continue
        e = {k: p.get(k) for k in ("id", "title", "title_en", "kind", "place", "lat", "lon", "t", "built", "note", "note_en")}
        e["first_seen"] = m.get("first_seen"); e["timeline"] = p.get("timeline", [])[:60]
        e["evn"] = {k: (p.get("evn") or {}).get(k) for k in ("distance_km", "coverage_pct", "peaks", "error")}
        e["sentinel"] = p.get("sentinel"); e["gauges"] = p.get("gauges"); e["ioda"] = p.get("ioda")
        if (p.get("evn") or {}).get("png") and time.time() - time.mktime(time.strptime(m["t"][:19], "%Y-%m-%dT%H:%M:%S")) < 21 * 86400:
            try: e["evn_png"] = "data:image/png;base64," + base64.b64encode(raw(f"events/{p['evn']['png']}", "events")).decode()
            except Exception as x: print("图", eid, x)
        evs.append(e)
    # 数据库单个文档上限 256 KiB：只给最近 3 个事件带图，超了就从最早的开始去掉图
    for e in sorted(evs, key=lambda e: e["t"])[:-3]: e.pop("evn_png", None)
    evd = {"updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "events": evs}
    for e in sorted(evs, key=lambda e: e["t"]):
        if len(json.dumps({**fs, "ev": evd}, ensure_ascii=False).encode()) < 230000: break
        e.pop("evn_png", None)
    json.dump(evd, open(f"{out}/live_ev.json", "w"), ensure_ascii=False)
    # 同时并进 live_fs.json 的 ev 字段：定时任务原本就写 live/fs，不用改任务也能把事件送到页面
    fs["ev"] = evd; json.dump(fs, open(f"{out}/live_fs.json", "w"), ensure_ascii=False)
    print("live_ev", os.path.getsize(f"{out}/live_ev.json"), "bytes,", len(evs), "events；live_fs", os.path.getsize(f"{out}/live_fs.json"), "bytes")
except Exception as e:
    print("事件证据包暂缺：", e)
