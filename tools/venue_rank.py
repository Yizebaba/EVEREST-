"""281 种灾害：每种找研究最集中、影响力最高的前三个期刊/会议，以及可作数据源或引用的数据集和数据论文。
数据来自 OpenAlex（公开学术数据库，2 亿多篇论文，api.openalex.org，免费、无需密钥）。在 GitHub 运行器上跑。

方法（可复现）：
  1. 用 tools/hazard_keywords.py 里每种灾害的第一个匹配词检索 2020 年以来的论文（article/review），按发表期刊或会议分组计数；
  2. 取论文数最多的 25 个来源里、该主题论文不少于 5 篇的，再按来源整体的 h 指数排序，取前三 → “该灾种的顶刊顶会”；
  3. 同一检索词下，类型为 dataset 的条目按被引次数取前五 → 可直接作数据源的公开数据集；
  4. 同一检索词下，发表在数据期刊（ESSD、Scientific Data、Geoscience Data Journal、Data in Brief）的论文按被引取前三 → 可引用的数据论文；
  5. 同一检索词下，2020 年以来被引最多的三篇论文 → 方法参考。
输出：venues.json
"""
import json, os, re, sys, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hazard_keywords import KW
HIPS = json.load(open(f"{ROOT}/data/taxonomy/hips2025_everest.json"))
OUT = sys.argv[1] if len(sys.argv) > 1 else "venues.json"
UA = {"user-agent": "everest-venue-rank (github.com/Yizebaba/EVEREST-)"}
SRC_CACHE = {}


def get(url):
    for i in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return json.loads(r.read())
        except Exception as e:
            if i == 3: raise
            time.sleep(2 + 3 * i)


def term(code):
    """检索词：匹配正则的第一个选项，去掉正则符号，括号取第一个分支。"""
    p = KW[code]
    def first(p):
        depth, buf = 0, ""
        for ch in p:
            if ch == "(": depth += 1
            elif ch == ")": depth -= 1
            if ch == "|" and depth == 0: break
            buf += ch
        while "(" in buf:
            a = buf.index("("); d = 0
            for k in range(a, len(buf)):
                d += buf[k] == "("; d -= buf[k] == ")"
                if d == 0: break
            buf = buf[:a] + first(buf[a + 1:k].lstrip("?:")) + buf[k + 1:]
        return buf
    t = re.sub(r"\\b|\\w[+*]|[?\\]", "", first(p)).replace("-", " ").strip()
    return t


def src_info(sid):
    if sid not in SRC_CACHE:
        s = get(f"https://api.openalex.org/sources/{sid.split('/')[-1]}?select=id,display_name,type,summary_stats,works_count,host_organization_name,homepage_url,is_oa")
        SRC_CACHE[sid] = {"name": s["display_name"], "type": s.get("type"), "h": (s.get("summary_stats") or {}).get("h_index"),
                          "if2": round((s.get("summary_stats") or {}).get("2yr_mean_citedness") or 0, 2), "publisher": s.get("host_organization_name"), "url": s.get("homepage_url"), "oa": s.get("is_oa")}
    return SRC_CACHE[sid]


def works(q, flt, sort="cited_by_count:desc", n=5, select="id,doi,display_name,publication_year,cited_by_count,primary_location,type"):
    u = "https://api.openalex.org/works?" + urllib.parse.urlencode({"search": q, "filter": flt, "sort": sort, "per-page": n, "select": select})
    return get(u).get("results", [])


def src_batch(ids):
    need = [x for x in ids if x not in SRC_CACHE]
    for k in range(0, len(need), 50):
        chunk = need[k:k + 50]
        r = get("https://api.openalex.org/sources?" + urllib.parse.urlencode({"filter": "openalex:" + "|".join(x.split("/")[-1] for x in chunk), "per-page": 50,
                                                                           "select": "id,display_name,type,summary_stats,host_organization_name,homepage_url,is_oa"}))
        for s in r.get("results", []):
            SRC_CACHE[s["id"]] = {"name": s["display_name"], "type": s.get("type"), "h": (s.get("summary_stats") or {}).get("h_index"),
                                  "if2": round((s.get("summary_stats") or {}).get("2yr_mean_citedness") or 0, 2), "publisher": s.get("host_organization_name"), "url": s.get("homepage_url"), "oa": s.get("is_oa")}


def one(h):
    c = h["code"]; q = term(c)
    q = f'"{q}"' if " " in q else q
    r = {"code": c, "label": h["label"], "label_zh": h["label_zh"], "family": h["family"], "family_zh": h["family_zh"], "cluster": h["cluster"], "query": q}
    try:
        g = get("https://api.openalex.org/works?" + urllib.parse.urlencode({"search": q, "filter": "from_publication_date:2020-01-01,type:article|review", "group_by": "primary_location.source.id", "per-page": 25}))
        r["papers_2020"] = g.get("meta", {}).get("count")
        cand = [x for x in g.get("group_by", []) if x.get("key") and x["key"] != "unknown" and x["count"] >= 5][:25]
        src_batch([x["key"] for x in cand])
        vs = [{**SRC_CACHE.get(x["key"], {"name": x.get("key_display_name"), "h": None}), "id": x["key"], "n": x["count"]} for x in cand]
        vs.sort(key=lambda v: (v.get("h") or 0), reverse=True)
        r["top_venues"] = vs[:3]; r["most_active"] = sorted(vs, key=lambda v: -v["n"])[:3]
        r["datasets"] = [{"title": w["display_name"], "doi": w.get("doi"), "year": w.get("publication_year"), "cites": w.get("cited_by_count"),
                          "repo": ((w.get("primary_location") or {}).get("source") or {}).get("display_name")} for w in works(q, "type:dataset", n=5)]
        r["data_papers"] = [{"title": w["display_name"], "doi": w.get("doi"), "year": w.get("publication_year"), "cites": w.get("cited_by_count"),
                             "journal": ((w.get("primary_location") or {}).get("source") or {}).get("display_name")}
                            for w in works(q, "primary_location.source.issn:1866-3516|1866-3508|2052-4463|2049-6060|2352-3409", n=3, select="id,doi,display_name,publication_year,cited_by_count,primary_location")]
        r["top_papers"] = [{"title": w["display_name"], "doi": w.get("doi"), "year": w.get("publication_year"), "cites": w.get("cited_by_count"),
                            "venue": ((w.get("primary_location") or {}).get("source") or {}).get("display_name")} for w in works(q, "from_publication_date:2020-01-01,type:article|review", n=3)]
    except Exception as e:
        r["err"] = str(e)[:200]
    print(c, q, r.get("papers_2020"), [v.get("name") for v in r.get("top_venues", [])], r.get("err", ""), flush=True)
    return r


from concurrent.futures import ThreadPoolExecutor
with ThreadPoolExecutor(6) as ex:
    res = list(ex.map(one, HIPS))
json.dump({"generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "method": __doc__, "hazards": res}, open(OUT, "w"), ensure_ascii=False, indent=1)
