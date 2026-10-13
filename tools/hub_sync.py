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
