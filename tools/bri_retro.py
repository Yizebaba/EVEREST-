"""一带一路样品：回溯测试。对 bri/retro_events.json 里的每个事件调用证据包脚本的 build()，结果写到 <输出目录>/<id>.json。
不存证、不进 index.json（这是测试，不是平台事件）。用法：python3 tools/bri_retro.py bri/retro_events.json <输出目录>
"""
import json, os, sys, traceback
sys.path.insert(0, os.path.dirname(__file__))
import evidence_pack as E

spec, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
E.OUT = out
for ev in json.load(open(spec))["events"]:
    print("build", ev["id"], flush=True)
    E.RECEIPTS.clear(); E.WAYBACK_DB = os.path.join(out, "wayback.json")
    try:
        E.WAYBACK_BUDGET[0] = 0   # 测试不去时光机存档
    except Exception:
        pass
    try:
        p = E.build(dict(ev))
        p["receipts"] = list({r["url"] + r["sha256"]: r for r in E.RECEIPTS}.values())
        p["retro_seed"] = ev["src"]
        json.dump(p, open(os.path.join(out, ev["id"] + ".json"), "w"), ensure_ascii=False, indent=1)
        print("  ", len(p["timeline"]), "条", flush=True)
    except Exception:
        traceback.print_exc()
