"""一带一路（Yizebaba/BRI-Empower）推演的种子材料：从那个公开仓库读已经自动生成好的种子文档（seeds/），按范围挑出来。
推演要求只用使用者自己写的文字（环境变量 MF_REQUIREMENT），本脚本不代写。

用法：python3 tools/mirofish_seed_bri.py <输出目录> [ALL|NPL|LAO|PAK]
输出：<输出目录>/seed/*.md、requirement.txt、context.txt、manifest.json（格式同 mirofish_seed.py，交给 mirofish_run.py）
"""
import json, os, re, sys, time, urllib.request

OUT = sys.argv[1]; SCOPE = (sys.argv[2] if len(sys.argv) > 2 else "ALL").strip().upper() or "ALL"
RAW = "https://raw.githubusercontent.com/Yizebaba/BRI-Empower/main/"
get = lambda p: urllib.request.urlopen(urllib.request.Request(RAW + p, headers={"user-agent": "EVEREST-mirofish"}), timeout=60).read()

REQ = os.environ.get("MF_REQUIREMENT", "").strip()
if len(REQ) < 10: sys.exit("缺少推演要求：请在网页表单里自己填写（至少 10 个字）")
idx = json.loads(get("seeds/index.json"))["scopes"]
keys = list(idx) if SCOPE == "ALL" else [k for k in re.split(r"[ ,]+", SCOPE) if k in idx]
if not keys: sys.exit("范围不对：" + SCOPE)
os.makedirs(os.path.join(OUT, "seed"), exist_ok=True)
files = {}
for i, k in enumerate(keys):
    for f in idx[k]["files"]:
        if i and f["path"].endswith("00_sources.md"): continue   # 来源说明只放一份
        name = f"{k}_{os.path.basename(f['path'])}"; b = get(f["path"])
        open(os.path.join(OUT, "seed", name), "wb").write(b); files[name] = len(b)
open(os.path.join(OUT, "requirement.txt"), "w").write(REQ)
open(os.path.join(OUT, "context.txt"), "w").write("种子文档由 BRI-Empower 自动从公开数据源生成（AidData、USGS、GDACS、NASA EONET、Google 新闻、IODA、美英旅行建议、UCDP/World Monitor），每条事实都注明来源和时间。范围：" + "、".join(idx[k]["name"] for k in keys) + "。推演结果单独保存、标注为推演。")
json.dump({"generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "project": "bri", "scope": keys, "files": files}, open(os.path.join(OUT, "manifest.json"), "w"), ensure_ascii=False, indent=1)
print("bri seed files:", files)
