"""一带一路样品：每个项目周边的实时态势（只用免费的一手来源，World Monitor 来源清单里同样在用的那些）。
跟着灾种扫描每 20 分钟跑一次，结果写到 events 分支 bri/live.json，连接器 everest_events(id="page:bri") 交给总览页。
只记录公开来源说了什么、什么时候说的；不判断成因，不预测，不发预警。

来源（全部免费、不要密钥）：
  USGS 地震目录（全球 M2.5 以上，近 7 天）、GDACS 全球灾害警报、NASA EONET 自然事件、
  Google 新闻 RSS（按项目名查近 7 天报道）、IODA 国家级网络中断告警、美国国务院和英国外交部旅行建议。
用法：python3 tools/bri_scan.py bri/projects.json <输出 live.json>
"""
import json, math, re, sys, time, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

PJ, OUT = sys.argv[1], sys.argv[2]
NOW = datetime.now(timezone.utc)
iso = lambda d: d.strftime("%Y-%m-%dT%H:%M:%SZ")
UA = {"user-agent": "EVEREST-bri-scan (github.com/Yizebaba/EVEREST-)"}
ERR = {}


def get(url, raw=False, timeout=40):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        b = r.read()
    return b if raw else json.loads(b)


def km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    return 6371 * 2 * math.asin(math.sqrt(math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2))


P = json.load(open(PJ))["projects"]
for p in P:   # 距离用项目范围的顶点（简化到约 200 m），够用
    p["_pts"] = [(y, x) for r in p["rings"] for x, y in r]


def near(lat, lon, p, lim):
    b = p["bbox"]; pad = lim / 100.0
    if not (b[0] - pad <= lat <= b[2] + pad and b[1] - pad / max(0.2, math.cos(math.radians(lat))) <= lon <= b[3] + pad / max(0.2, math.cos(math.radians(lat)))):
        return None
    d = min(km((lat, lon), q) for q in p["_pts"])
    return round(d, 1) if d <= lim else None


hits = {p["id"]: [] for p in P}
def add(pid, item): hits[pid].append(item)

# 1 USGS：近 7 天全球 M2.5+，项目 150 km 内
try:
    for f in get("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_week.geojson")["features"]:
        lo, la = f["geometry"]["coordinates"][:2]; pr = f["properties"]
        for p in P:
            d = near(la, lo, p, 150)
            if d is not None:
                add(p["id"], {"t": iso(datetime.fromtimestamp(pr["time"] / 1000, timezone.utc)), "src": "USGS 地震目录", "kind": "地震" if pr.get("type") == "earthquake" else (pr.get("type") or ""),
                              "text": f"M{pr.get('mag')} {pr.get('type')} · {pr.get('place')}", "km": d, "url": pr.get("url")})
except Exception as e: ERR["usgs"] = str(e)[:120]

# 2 GDACS：近 14 天全部警报，项目 300 km 内（洪水、气旋范围大，只给距中心点的距离）
try:
    a = (NOW - timedelta(days=14)).strftime("%Y-%m-%d"); b = NOW.strftime("%Y-%m-%d")
    for f in get(f"https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH?fromDate={a}&toDate={b}&alertlevel=Green;Orange;Red")["features"]:
        lo, la = f["geometry"]["coordinates"][:2]; pr = f["properties"]
        for p in P:
            d = near(la, lo, p, 300)
            if d is not None:
                add(p["id"], {"t": (pr.get("fromdate") or "")[:19] + "Z", "src": "GDACS", "kind": pr.get("eventtype"),
                              "text": f"{pr.get('alertlevel')} 级 · {pr.get('name') or pr.get('eventname')}", "km": d, "url": (pr.get("url") or {}).get("report")})
except Exception as e: ERR["gdacs"] = str(e)[:120]

# 3 NASA EONET：近 30 天的自然事件（火山、风暴、洪水、滑坡、野火等），项目 150 km 内
try:
    for ev in get("https://eonet.gsfc.nasa.gov/api/v3/events?days=30")["events"]:
        for g in ev.get("geometry", [])[-1:]:
            c = g["coordinates"]
            if g["type"] != "Point": c = c[0][0] if isinstance(c[0][0], list) else c[0]
            for p in P:
                d = near(c[1], c[0], p, 150)
                if d is not None:
                    add(p["id"], {"t": g["date"][:19] + "Z", "src": "NASA EONET", "kind": ",".join(x["title"] for x in ev.get("categories", [])),
                                  "text": ev["title"], "km": d, "url": (ev.get("sources") or [{}])[0].get("url")})
except Exception as e: ERR["eonet"] = str(e)[:120]

# 4 Google 新闻 RSS：按项目名查近 7 天的报道（新闻是线索，不是权威记录）
NEWSQ = {"aiddata-38360": '"Rasuwagadhi" OR "Syaphrubesi"', "aiddata-53125": '"Rasuwagadhi" OR "Timure"', "aiddata-53716": '"Upper Trishuli" OR "Trishuli 3A"',
         "aiddata-38705": '"Trishuli" transmission line', "aiddata-72338": '"Kerung-Kathmandu" OR "Kerung Kathmandu railway"', "aiddata-85304": '"Laos-China Railway" OR "China-Laos Railway"',
         "aiddata-63762": '"Nam Ou" hydropower', "aiddata-35739": '"Karakoram Highway" OR "KKH" Hunza', "aiddata-54424": '"Karakoram Highway" Thakot OR Havelian OR Mansehra',
         "aiddata-37233": '"Karot" hydropower', "aiddata-92475": '"Gwadar port" OR "Gwadar"'}
INC = re.compile(r"flood|landslide|avalanche|earthquake|quake|glacial|debris|collapse|blocked|closed|suspend|halt|attack|blast|explosion|protest|strike|killed|dead|injur|missing|accident|derail|fire|storm|cyclone|outage", re.I)
for p in P:
    q = NEWSQ.get(p["id"])
    if not q: continue
    try:
        u = "https://news.google.com/rss/search?" + urllib.parse.urlencode({"q": q + " when:7d", "hl": "en", "gl": "US", "ceid": "US:en"})
        root = ET.fromstring(get(u, raw=True))
        for it in root.iter("item"):
            ti = (it.findtext("title") or "").strip(); pd = it.findtext("pubDate")
            try: t = iso(datetime.strptime(pd, "%a, %d %b %Y %H:%M:%S %Z").replace(tzinfo=timezone.utc))
            except Exception: continue
            add(p["id"], {"t": t, "src": "新闻（Google 新闻 RSS）", "kind": "事件相关" if INC.search(ti) else "一般报道", "text": ti[:200], "url": it.findtext("link")})
        time.sleep(1.5)
    except Exception as e: ERR["news:" + p["id"]] = str(e)[:120]

# 5 IODA：项目所在国近 7 天的国家级网络中断告警
ioda = {}
for iso2 in sorted({ {"NPL": "NP", "LAO": "LA", "PAK": "PK"}[p["country"]] for p in P }):
    try:
        a, b = int((NOW - timedelta(days=7)).timestamp()), int(NOW.timestamp())
        x = get(f"https://api.ioda.inetintel.cc.gatech.edu/v2/outages/alerts?entityType=country&entityCode={iso2}&from={a}&until={b}&limit=50")
        L = x.get("data") or []
        ioda[iso2] = {"n": len(L), "alerts": [{"t": iso(datetime.fromtimestamp(z["time"], timezone.utc)), "src": z.get("datasource"), "level": z.get("level"), "cond": z.get("condition"),
                                               "value": z.get("value"), "base": z.get("historyValue")} for z in L[:12]]}
    except Exception as e: ERR["ioda:" + iso2] = str(e)[:120]

# 6 旅行建议：美国国务院（级别 1–4）和英国外交部（最近更新时间和摘要）
adv = {}
try:
    root = ET.fromstring(get("https://travel.state.gov/_res/rss/TAsTWs.xml", raw=True))
    for it in root.iter("item"):
        ti = it.findtext("title") or ""
        for iso3, nm in (("NPL", "Nepal"), ("LAO", "Laos"), ("PAK", "Pakistan")):
            if ti.startswith(nm + " "):
                m = re.search(r"Level (\d)", ti)
                adv.setdefault(iso3, {})["us"] = {"level": int(m.group(1)) if m else None, "title": ti.strip(), "t": it.findtext("pubDate"), "url": it.findtext("link")}
except Exception as e: ERR["us_advisory"] = str(e)[:120]
for iso3, slug in (("NPL", "nepal"), ("LAO", "laos"), ("PAK", "pakistan")):
    try:
        x = get(f"https://www.gov.uk/api/content/foreign-travel-advice/{slug}")
        d = x.get("details") or {}
        adv.setdefault(iso3, {})["uk"] = {"t": x.get("public_updated_at"), "change": (d.get("change_description") or "")[:300], "url": "https://www.gov.uk/foreign-travel-advice/" + slug}
    except Exception as e: ERR["uk_advisory:" + iso3] = str(e)[:120]

out = {"generated": iso(NOW), "note": "只记录公开来源说了什么、什么时候说的；不判断成因，不预测，不发预警。距离是到项目范围（AidData）最近点的直线距离。",
       "projects": {}, "countries": {}, "errors": ERR}
for p in P:
    L = sorted(hits[p["id"]], key=lambda x: x["t"], reverse=True)
    seen = set(); L = [x for x in L if not ((x["src"], x["text"]) in seen or seen.add((x["src"], x["text"])))]
    out["projects"][p["id"]] = {"n": len(L), "n_incident": sum(1 for x in L if x["src"] != "新闻（Google 新闻 RSS）" or x["kind"] == "事件相关"), "items": L[:40]}
for iso3, iso2 in (("NPL", "NP"), ("LAO", "LA"), ("PAK", "PK")):
    out["countries"][iso3] = {"ioda": ioda.get(iso2), "advisory": adv.get(iso3)}
json.dump(out, open(OUT, "w"), ensure_ascii=False, separators=(",", ":"))
print("bri live:", {k: v["n"] for k, v in out["projects"].items()}, "errors:", ERR)
