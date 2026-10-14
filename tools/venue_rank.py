"""281 种灾害：每种找研究最集中、影响力最高的前三个期刊/会议，以及可作数据源或引用的数据集和数据论文。
数据来自 OpenAlex（公开学术数据库，2 亿多篇论文，api.openalex.org，免费、无需密钥）。在 GitHub 运行器上跑。

方法（可复现）：
  1. 用 tools/hazard_keywords.py 里每种灾害的第一个匹配词检索 2020 年以来的论文（article/review），按发表期刊或会议分组计数；
  2. 取论文数最多的 25 个来源里、该主题论文不少于 5 篇的期刊或会议（排除 Zenodo 这类存储库），
     再去掉综合性大刊（名单见 MULTI，如 PLoS ONE、Scientific Reports、Nature Communications），按来源整体的 h 指数排序取前三
     → “该灾种的专业顶刊顶会”；综合性大刊单独列出（multidisciplinary）；
  3. 同一检索词下，发表在数据期刊（ESSD、Scientific Data、Geoscience Data Journal、Data in Brief）的论文按被引取前三 → 可引用的数据论文；
  4. 同一检索词下，2020 年以来被引最多的三篇论文 → 方法参考。
输出：venues.json
增量运行：OpenAlex 按额度计费（无密钥每天约 100 次检索，免费密钥约 1000 次；每个灾种 3 次检索）。
已有结果的灾种跳过；额度用完（HTTP 429）就停，下次接着跑。可选环境变量 OPENALEX_API_KEY（openalex.org/settings/api）。
"""
import json, os, re, sys, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hazard_keywords import KW
HIPS = json.load(open(f"{ROOT}/data/taxonomy/hips2025_everest.json"))
OUT = sys.argv[1] if len(sys.argv) > 1 else "venues.json"
UA = {"user-agent": "everest-venue-rank (github.com/Yizebaba/EVEREST-)"}
SRC_CACHE = {}
KEY = os.environ.get("OPENALEX_API_KEY", "")
PREV = sys.argv[2] if len(sys.argv) > 2 else ""
STOP = []


class Budget(Exception): pass


MULTI = {"plos one", "scientific reports", "nature communications", "nature", "science", "proceedings of the national academy of sciences",
         "science advances", "ieee access", "sustainability", "heliyon", "cureus", "peerj", "royal society open science", "frontiers in public health",
         "international journal of environmental research and public health", "applied sciences", "sensors", "remote sensing", "the lancet",
         "bmj", "bmj open", "communications earth & environment", "nature sustainability", "environmental research letters", "plos medicine", "elife"}
VENUE_TYPES = {"journal", "conference", "book series"}


def get(url):
    if STOP: raise Budget("stopped")
    if KEY: url += ("&" if "?" in url else "?") + "api_key=" + KEY
    for i in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return json.loads(r.read())
        except Exception as e:
            if getattr(e, "code", 0) == 429 and i >= 1:
                STOP.append(1); raise Budget("HTTP 429: OpenAlex 当日额度用完")
            if i == 3: raise
            time.sleep(2 + 3 * i)


# 正则直接转出来不像检索词的，手工给检索词（学术文献里的常用说法）
QUERY = {"MH0204": "sand haze", "MH0307": "extratropical cyclone", "MH0308": "subtropical cyclone", "MH0505": "hoarfrost", "MH0510": "spring thaw flood",
         "MH0600": "flood disaster", "MH0602": "estuarine flooding", "MH0606": "inundation", "MH0610": "snowmelt flood", "MH0701": "rogue wave",
         "MH0707": "ice floe", "ET0102": "ionospheric disturbance", "ET0202": "ultraviolet radiation exposure", "ET0204": "rocket debris re-entry",
         "GH0201": "lava flow", "GH0300": "landslide", "GH0305": "rock topple", "GH0310": "expansive soil", "GH0311": "ground fissure",
         "GH0401": "soft soil settlement", "GH0406": "sand encroachment", "EN0102": "industrial emissions", "EN0106": "nonpoint source pollution",
         "EN0207": "mangrove loss", "EN0303": "soil salinization", "CH0400": "asphyxiation", "CH0602": "falsified medicines",
         "CH0603": "methanol poisoning", "CH0604": "opioid overdose", "BI0102": "bloodborne pathogens", "BI0108": "vector-borne disease",
         "BI0110": "waterborne disease", "BI0111": "cryptosporidiosis", "BI0112": "cysticercosis", "BI0113": "zoonotic disease", "BI0205": "COVID-19",
         "BI0210": "Escherichia coli outbreak", "BI0218": "listeriosis", "BI0234": "shigellosis", "BI0236": "SARS coronavirus", "BI0238": "trypanosomiasis",
         "BI0306": "foot-and-mouth disease", "BI0310": "peste des petits ruminants", "BI0313": "oyster disease", "BI0401": "pest outbreak",
         "BI0502": "rice blast", "BI0604": "human-leopard conflict", "TL0106": "cyberbullying", "TL0206": "supply chain disruption",
         "TL0210": "water supply interruption", "TL0214": "sewer overflow", "TL0302": "environmental pollution", "TL0305": "fire disaster",
         "TL0502": "solid waste", "TL0507": "e-waste", "TL0602": "radioactive contamination", "TL0603": "uranium mining",
         "SO0101": "armed conflict", "SO0102": "insurgency", "SO0201": "unexploded ordnance", "SO0202": "conflict pollution", "SO0301": "violence",
         "SO0302": "crowd crush", "MH0203": "haze pollution", "MH0303": "gale wind", "MH0306": "cyclone disaster", "MH0509": "atmospheric icing"}


def term(code):
    """检索词：优先用 QUERY 里的手工词；否则取匹配正则的第一个选项，去掉正则符号，括号取第一个分支。"""
    if code in QUERY: return QUERY[code]
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
        vs = [v for v in vs if v.get("type") in VENUE_TYPES]
        vs.sort(key=lambda v: (v.get("h") or 0), reverse=True)
        r["top_venues"] = [v for v in vs if (v.get("name") or "").lower() not in MULTI][:3]
        r["multidisciplinary"] = [v for v in vs if (v.get("name") or "").lower() in MULTI][:3]; r["most_active"] = sorted(vs, key=lambda v: -v["n"])[:3]
        r["data_papers"] = [{"title": w["display_name"], "doi": w.get("doi"), "year": w.get("publication_year"), "cites": w.get("cited_by_count"),
                             "journal": ((w.get("primary_location") or {}).get("source") or {}).get("display_name")}
                            for w in works(q, "primary_location.source.issn:1866-3516|1866-3508|2052-4463|2049-6060|2352-3409", n=3, select="id,doi,display_name,publication_year,cited_by_count,primary_location")]
        r["top_papers"] = [{"title": w["display_name"], "doi": w.get("doi"), "year": w.get("publication_year"), "cites": w.get("cited_by_count"),
                            "venue": ((w.get("primary_location") or {}).get("source") or {}).get("display_name")} for w in works(q, "from_publication_date:2020-01-01,type:article|review", n=3)]
    except Exception as e:
        r["err"] = str(e)[:200]
    print(c, q, r.get("papers_2020"), [v.get("name") for v in r.get("top_venues", [])], r.get("err", ""), flush=True)
    return r


old = {}
if PREV and os.path.exists(PREV):
    try: old = {h["code"]: h for h in json.load(open(PREV))["hazards"] if "multidisciplinary" in h and not h.get("err")}
    except Exception as e: print("prev unreadable", e)
todo = [h for h in HIPS if h["code"] not in old]
print(f"已有 {len(old)}，待查 {len(todo)}，密钥 {'有' if KEY else '无'}", flush=True)
from concurrent.futures import ThreadPoolExecutor
with ThreadPoolExecutor(3) as ex:
    new = {r["code"]: r for r in ex.map(one, todo)}
res = [old.get(h["code"]) or new.get(h["code"]) for h in HIPS]
done = sum(1 for r in res if r and not r.get("err"))
json.dump({"generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "method": __doc__, "done": done, "total": len(HIPS), "hazards": res},
          open(OUT, "w"), ensure_ascii=False, indent=1)
print(f"完成 {done}/{len(HIPS)}", flush=True)
