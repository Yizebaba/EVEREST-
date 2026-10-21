"""一带一路（Yizebaba/BRI-Full-Scope-Foresight）推演的种子材料：从那个公开仓库读已经自动生成好的种子文档（seeds/），按范围挑出来。
推演要求只用使用者自己写的文字（环境变量 MF_REQUIREMENT），本脚本不代写。

用法：python3 tools/mirofish_seed_bri.py <输出目录> <ISO3[,ISO3…]>（150 个共建国家之一或多个）
输出：<输出目录>/seed/*.md、requirement.txt、context.txt、manifest.json（格式同 mirofish_seed.py，交给 mirofish_run.py）
"""
import json, os, re, sys, time, urllib.request

OUT = sys.argv[1]; SCOPE = (sys.argv[2] if len(sys.argv) > 2 else "").strip().upper()
RAW = "https://raw.githubusercontent.com/Yizebaba/BRI-Full-Scope-Foresight/main/"
get = lambda p: urllib.request.urlopen(urllib.request.Request(RAW + p, headers={"user-agent": "EVEREST-mirofish"}), timeout=60).read()

REQ = os.environ.get("MF_REQUIREMENT", "").strip()
if len(REQ) < 10: sys.exit("缺少推演要求：请在网页表单里自己填写（至少 10 个字）")
idx = json.loads(get("seeds/index.json"))["scopes"]
JOB = os.environ.get("MF_JOB", "").strip(); SEL = [x for x in os.environ.get("MF_SEEDS", "").split(",") if x.strip()]
os.makedirs(os.path.join(OUT, "seed"), exist_ok=True)
files = {}
if JOB:   # 网页提交：只用使用者勾选的种子文档（可以一份都不选，只用自己上传的资料）
    files_src = [((p.split("/")[1] + "_" if p.count("/") == 2 else "") + os.path.basename(p), p) for p in SEL]
    keys = sorted({p.split("/")[1] for p in SEL if p.count("/") == 2})
else:     # 仓库主人手动运行：按国家取全部种子文档
    keys = [k for k in re.split(r"[ ,]+", SCOPE) if k in idx][:5]
    if not keys: sys.exit("范围不对：" + SCOPE)
    files_src = [("00_sources.md", "seeds/00_sources.md")] + [(f"{k}_{os.path.basename(f['path'])}", f["path"]) for k in keys for f in idx[k]["files"]]
for name, path in files_src:
    b = get(path)
    open(os.path.join(OUT, "seed", name), "wb").write(b); files[name] = len(b)
open(os.path.join(OUT, "requirement.txt"), "w").write(REQ)
open(os.path.join(OUT, "context.txt"), "w").write("种子文档由 BRI-Empower 自动从公开数据源生成（AidData、USGS、GDACS、NASA EONET、Google 新闻、IODA、美英旅行建议、UCDP/World Monitor），每条事实都注明来源和时间。国家：" + "、".join(idx[k]["name"] for k in keys) + "。推演结果单独保存、标注为推演。" if keys else "推演结果单独保存、标注为推演。")
json.dump({"generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "project": "bri", "scope": keys, "files": files}, open(os.path.join(OUT, "manifest.json"), "w"), ensure_ascii=False, indent=1)
print("bri seed files:", files)
