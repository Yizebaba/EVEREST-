"""用灾种扫描的实测结果（events 分支 hazards/scan.json）生成 docs/HAZARDS_281.md。
用法：python3 tools/hips_report.py scan.json"""
import json, sys, os
from collections import Counter
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sc = json.load(open(sys.argv[1]))
ST = {"local": "本地有记录", "global": "外地有记录", "observed": "有持续观测", "ok_none": "来源正常，90 天无记录", "key": "需密钥", "fail": "来源失败"}
EXPL = {"local": "近 90 天在尼泊尔、西藏或喜马拉雅一带有记录", "global": "近 90 天只在别的地区有记录（接口能用，本地没发生或没报道）",
        "observed": "有卫星或站网在持续观测，但没有“发生了”的记录（例如 Sentinel-5P 大气成分）", "ok_none": "至少一个来源实测能用，近 90 天没有相关记录",
        "key": "唯一的来源需要密钥，还没配置", "fail": "所有来源这次都没取到"}
H = sc["hazards"]; cnt = Counter(h["state"] for h in H)
md = ["# 281 种灾害：逐个实测", "",
      f"灾害分类取自联合国减灾署和国际科学理事会《灾害信息档案》2025 版（UNDRR-ISC HIPs）：281 种，8 大类。下表由每小时运行的灾种扫描（`.github/workflows/hazards.yml` → `tools/hazard_scan.py`）实测生成，最近一次：{sc['updated']}（UTC）。",
      "", "每种灾害至少有一个实测能用的公开来源；新闻层（尼泊尔英文媒体、谷歌新闻、ReliefWeb RSS）用逐条写的匹配词（`tools/hazard_keywords.py`）覆盖全部 281 种。只记录已经发生、被公开来源记下的事，不预测。", "", "本文件是某一次扫描的快照；每小时的最新结果在 events 分支 [`hazards/scan.json`](https://github.com/Yizebaba/EVEREST-/blob/events/hazards/scan.json)，总览页“证据链 → 灾种 281”实时显示。", "",
      "## 状态", "", "| 状态 | 数量 | 含义 |", "|---|---|---|"]
for k in ST:
    if cnt[k]: md.append(f"| {ST[k]} | {cnt[k]} | {EXPL[k]} |")
md += ["", "## 数据源实测", "", "| 来源 | 结果 | 本次条数 | 其中本地 | 说明 |", "|---|---|---|---|---|"]
for k, v in sc["sources"].items():
    res = {"ok": "正常", "key": "需密钥", "fail": "失败"}.get(v["state"], v["state"])
    md.append(f"| {k} | {res} | {v.get('n', '')} | {v.get('local', '')} | {(v.get('err') or v.get('need') or '')[:80]} |")
md.append("")
fams = list(dict.fromkeys(h["family_zh"] for h in H))
for f in fams:
    L = [h for h in H if h["family_zh"] == f]; c2 = Counter(h["state"] for h in L)
    md += [f"## {f}（{L[0]['family']}）· {len(L)} 种", "", " · ".join(f"{ST[k]} {c2[k]}" for k in ST if c2[k]), "",
           "| 编码 | 灾害 | 状态 | 90 天记录（本地） | 实测能用的来源 | 最近一条 |", "|---|---|---|---|---|---|"]
    for h in L:
        last = (h.get("latest") or "")[:10] + " " + (h.get("latest_title") or "").replace("|", "/")[:70] if h.get("latest") else (h.get("observed") or "")[:60]
        md.append(f"| {h['code']} | {h['label_zh']}（{h['label']}） | {ST[h['state']]} | {h['n_90d']}（{h['n_local_90d']}） | {'、'.join(h['tested_ok'])} | {last} |")
    md.append("")
open(f"{R}/docs/HAZARDS_281.md", "w").write("\n".join(md))
print(dict(cnt))
