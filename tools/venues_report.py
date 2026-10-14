"""venues.json → HAZARD_VENUES.md：281 种灾害按 8 大类，每种列专业顶刊顶会前三、可引用的数据论文、高被引方法论文。
用法：python3 tools/venues_report.py venues.json HAZARD_VENUES.md"""
import json, sys

d = json.load(open(sys.argv[1]))
H = [h for h in d["hazards"] if h]
out = []
w = out.append
done = [h for h in H if h.get("src") == "openalex+crossref" and not h.get("err")]
pend = [h for h in done if h.get("venues_pending")]
w("# 281 种灾害：各灾种的专业顶刊顶会和可引用数据\n")
w(f"自动生成于 {d['generated']}，数据论文已查 **{len(done)}/{d.get('total', 281)}** 种，期刊排名已完成 **{len(done) - len(pend)}** 种（期刊排名用 OpenAlex，按天计额度，每天自动续跑，补齐为止）。"
  "生成脚本 `tools/venue_rank.py` + `tools/venues_report.py`，原始数据 `hazards/venues.json`（events 分支）。\n")
w("## 方法\n")
w("1. 每种灾害一个英文检索词（多数取自 `tools/hazard_keywords.py` 的匹配词，部分手工改成学术常用说法，见 `venue_rank.py` 的 `QUERY`）。")
w("2. 在 OpenAlex 检索 2020 年以来的论文和综述，按发表的期刊/会议分组计数，取该主题论文 ≥ 5 篇的期刊或会议（排除 Zenodo 等存储库）。")
w("3. 去掉综合性大刊（PLoS ONE、Scientific Reports、Nature Communications、Nature、Science、PNAS 等，单独列出），按期刊整体 h 指数排前三 → **专业顶刊**。")
w("4. 数据论文（Crossref）：标题里要出现检索词中的实词；同一检索词在 ESSD、Scientific Data、Geoscience Data Journal、Data in Brief 四本数据期刊里检索相关度最高的三篇 → **可作数据源或引用的数据集**。")
w("5. 方法论文（Crossref）：同一检索词 2020 年以来相关度前 20 篇里被引最多的三篇。\n")
w("**局限**：h 指数衡量期刊整体影响力，不是该灾种的专业排名；检索词有歧义时会混进无关期刊（例如 lightning 混进分子科学期刊）。"
  "这份表是找文献和数据的起点，用到具体期刊或数据前请人工确认。会议（如 AGU、EGU、ISCRAM）在 OpenAlex 里收录不全，排名以期刊为主。\n")

fams = []
for h in H:
    if h["family"] not in fams: fams.append(h["family"])
w("## 总览：各大类出现最多的专业期刊\n")
w("| 大类 | 已完成 | 出现最多的专业期刊（次数） |\n|---|---|---|")
for f in fams:
    hs = [h for h in done if h["family"] == f]
    c = {}
    for h in hs:
        for v in h.get("top_venues") or []: c[v["name"]] = c.get(v["name"], 0) + 1
    top = "；".join(f"{k}（{n}）" for k, n in sorted(c.items(), key=lambda x: -x[1])[:5])
    zh = next((h["family_zh"] for h in H if h["family"] == f), f)
    w(f"| {zh} | {len(hs)}/{sum(1 for h in H if h['family'] == f)} | {top or '—'} |")
w("")


def link(x):
    t = (x.get("title") or "").replace("|", "/")[:110]
    return f"[{t}]({x['doi']})" if x.get("doi") else t


for f in fams:
    zh = next((h["family_zh"] for h in H if h["family"] == f), f)
    w(f"## {zh}（{f}）\n")
    w("| 编码 | 灾种 | 检索词 | 2020 年以来论文 | 专业顶刊前三（h 指数 · 该主题篇数） | 可引用数据论文 |\n|---|---|---|---|---|---|")
    for h in H:
        if h["family"] != f: continue
        if h not in done:
            w(f"| {h['code']} | {h['label_zh']} | {h.get('query', '')} | 待查 | | |"); continue
        tv = "待查（OpenAlex 额度）" if h.get("venues_pending") else ("<br>".join(f"{v['name']}（h{v.get('h')} · {v['n']}）" for v in h["top_venues"]) or "—")
        dp = "<br>".join(link(x) + f"（{x.get('journal', '')} {x.get('year', '')}，被引 {x.get('cites')}）" for x in h.get("data_papers", [])) or "—"
        w(f"| {h['code']} | {h['label_zh']} | `{h['query']}` | {h.get('papers_2020') or '—'} | {tv} | {dp} |")
    w("")
    w("<details><summary>高被引方法论文</summary>\n")
    for h in H:
        if h["family"] != f or h not in done or not h.get("top_papers"): continue
        w(f"- **{h['code']} {h['label_zh']}**：" + "；".join(link(x) + f"（{x.get('venue') or ''} {x.get('year')}）" for x in h["top_papers"]))
    w("\n</details>\n")
open(sys.argv[2], "w").write("\n".join(out))
print(len(done), "done")
