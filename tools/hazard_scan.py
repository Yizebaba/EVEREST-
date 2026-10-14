"""281 种灾害（UNDRR-ISC 2025）逐个扫描公开数据源。每小时在 GitHub 运行器上跑，只做小量取数。

输出（写到 events 分支 hazards/）：
  scan.json     每种灾害：用了哪些来源、每个来源这次实测的结果（成功/失败/需密钥、条数、最新时间）、状态
  records.json  所有来源取到的记录（时间、坐标、来源、灾害编码），保留 90 天；证据包按时间和距离把它们挂到事件上
  scan_events.json  需要单独做证据包的事件候选（喜马拉雅高山区的自然灾害、或造成 3 人以上死亡的事件）

只记录已经发生、被公开来源记下的事；不预测。
"""
import csv, io, json, math, os, re, sys, time, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone

OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
NOW = datetime.now(timezone.utc)
UA = {"user-agent": "everest-hazard-scan (github.com/Yizebaba/EVEREST-)", "accept": "application/json, */*"}
BOX = (26.3, 31.5, 79.5, 92.5)   # 喜马拉雅范围 s, n, w, e
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HIPS = json.load(open(f"{ROOT}/data/taxonomy/hips2025_everest.json"))
CODES = {h["code"]: h for h in HIPS}


def iso(d): return d.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
def P(s): return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)
def inbox(la, lo): return la is not None and lo is not None and BOX[0] <= la <= BOX[1] and BOX[2] <= lo <= BOX[3]


def get(url, data=None, headers=None, timeout=60, raw=False):
    req = urllib.request.Request(url, data=data, headers={**UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        b = r.read()
    return b if raw else json.loads(b)


RECS = []      # 这次取到的记录
RES = {}       # 来源 → 实测结果


def source(name, need=None):
    """装饰器：执行来源函数，记录实测结果。need 是需要的环境变量（密钥），没配置时直接记为“需密钥”。"""
    def deco(fn):
        def run():
            if need and not os.environ.get(need):
                RES[name] = {"state": "key", "need": need}; return
            t = time.time(); n0 = len(RECS)
            try:
                info = fn() or {}
                new = RECS[n0:]
                for r in new: r["src"] = name
                RES[name] = {"state": "ok", "n": len(new), "local": sum(1 for r in new if r.get("local")), "latest": max((r["t"] for r in new), default=None), "sec": round(time.time() - t, 1), **info}
            except Exception as e:
                RES[name] = {"state": "fail", "err": str(e)[:200], "sec": round(time.time() - t, 1)}
            print(name, RES[name].get("state"), RES[name].get("n"), RES[name].get("err", "")[:80], flush=True)
        run.name = name; SOURCES.append(run); return run
    return deco


SOURCES = []


def rec(codes, t, title, lat=None, lon=None, url=None, rid=None, **kw):
    RECS.append({"codes": codes, "t": t, "title": str(title)[:200], "lat": lat, "lon": lon, "url": url, "id": rid, "local": inbox(lat, lon) if lat is not None else kw.pop("local", False), **kw})


# ---------- 尼泊尔政府 BIPAD：事件库（47 类）和警报 ----------
BIPAD_HZ = {17: ["GH0300", "GH0304"], 11: ["MH0604", "MH0600"], 4: ["TL0402"], 20: ["BI0605"], 23: ["MH0102"], 10: ["TL0305"], 7: ["TL0402"],
            14: ["MH0402"], 24: ["MH0301", "MH0304"], 6: ["MH0502"], 8: ["GH0101"], 15: ["TL0401"], 43: ["CH0300"], 13: ["MH0404"], 42: ["TL0602"],
            9: ["BI0101", "BI0103", "BI0108", "BI0110"], 41: ["TL0301", "CH0901"], 5: ["TL0204"], 3: ["MH0801"], 1: ["TL0401"], 28: ["MH0606"], 35: ["BI0245"],
            26: ["MH0607"], 40: ["TL0304"], 39: ["BI0104", "CH0601"], 46: ["TL0402"], 29: ["GH0403"], 2: ["BI0604"], 12: ["EN0205"], 30: ["GH0201"],
            44: ["BI0501", "BI0502", "BI0503"], 37: ["EN0103", "TL0302"], 27: ["MH0501"], 22: ["MH0103"], 32: ["TL0307"], 34: ["TL0405"], 31: ["TL0309", "TL0207"],
            25: ["MH0401"], 33: ["BI0244", "BI0205"], 21: ["MH0406"], 36: ["EN0201"], 19: ["MH0402"]}


@source("BIPAD 灾害事件库")
def bipad_incident():
    names = {h["id"]: h["title"] for h in get("https://bipadportal.gov.np/api/v1/hazard/?format=json&limit=200")["results"]}
    since = (NOW - timedelta(days=30)).strftime("%Y-%m-%d")
    url = f"https://bipadportal.gov.np/api/v1/incident/?format=json&ordering=-incident_on&limit=500&incident_on__gt={since}&expand=loss"
    rows = get(url, timeout=120).get("results", [])
    for r in rows:
        c = (r.get("point") or {}).get("coordinates") or [None, None]; L = r.get("loss") or {}
        if not isinstance(L, dict): L = {}
        rec(BIPAD_HZ.get(r.get("hazard"), []), iso(P(r["incidentOn"])), r.get("title"), c[1], c[0], f"https://bipadportal.gov.np/incidents/{r['id']}", f"bipad-i-{r['id']}",
            hazard_name=names.get(r.get("hazard")), deaths=L.get("peopleDeathCount") or 0, injured=L.get("peopleInjuredCount") or 0, missing=L.get("peopleMissingCount") or 0, local=True)
    return {"window_days": 30, "hazard_types": len(names)}


BIPAD_AL = [(r"flood", ["MH0604"]), (r"landslide", ["GH0300"]), (r"avalanche", ["MH0801"]), (r"forest fire|wildfire", ["EN0205"]), (r"lightning|thunderbolt", ["MH0102"]),
            (r"cold wave", ["MH0502"]), (r"snow", ["MH0405"]), (r"earthquake", ["GH0101"]), (r"heavy rainfall", ["MH0402"]), (r"pollution", ["EN0103"]), (r"road closed", ["TL0405", "TL0207"])]


@source("BIPAD 警报")
def bipad_alert():
    for r in get("https://bipadportal.gov.np/api/v1/alert/?format=json&ordering=-started_on&limit=100").get("results", []):
        c = (r.get("point") or {}).get("coordinates") or [None, None]
        codes = next((cs for pat, cs in BIPAD_AL if re.search(pat, r.get("title") or "", re.I)), [])
        rec(codes, iso(P(r["startedOn"])), r.get("title"), c[1], c[0], None, f"bipad-a-{r['id']}", local=True)


@source("BIPAD 空气质量站")
def bipad_pollution():
    rows = get("https://bipadportal.gov.np/api/v1/pollution-stations/?format=json&limit=100").get("results", [])
    for r in rows:
        c = (r.get("point") or {}).get("coordinates") or [None, None]
        aqi = r.get("aqi")
        if aqi is not None and float(aqi) >= 150:
            rec(["EN0103", "MH0203", "EN0104"], iso(P(r.get("dateTime") or r.get("modifiedOn") or iso(NOW))), f"{r.get('name') or r.get('title')} AQI {aqi}", c[1], c[0], None, f"bipad-p-{r.get('id')}", local=True)
    return {"stations": len(rows)}


# ---------- NASA EONET（自然事件，含喜马拉雅范围和全球） ----------
EONET = {"drought": ["MH0401"], "dustHaze": ["MH0201", "MH0203", "MH0204", "MH0205"], "earthquakes": ["GH0101"], "floods": ["MH0600"], "landslides": ["GH0300"],
         "manmade": ["TL0304", "TL0305"], "seaLakeIce": ["MH0706", "MH0707"], "severeStorms": ["MH0306", "MH0307", "MH0308", "MH0309"], "snow": ["MH0405"],
         "tempExtremes": ["MH0501", "MH0502"], "volcanoes": ["GH0201", "GH0202", "GH0203", "GH0204", "GH0205"], "waterColor": ["EN0403", "BI0603"], "wildfires": ["EN0205"]}


@source("NASA EONET")
def eonet():
    seen = set()
    for url in ("https://eonet.gsfc.nasa.gov/api/v3/events?bbox=79.5,31.5,92.5,26.3&days=60&status=all", "https://eonet.gsfc.nasa.gov/api/v3/events?days=14&status=all&limit=300"):
        for e in get(url).get("events", []):
            if e["id"] in seen: continue
            seen.add(e["id"]); g = (e.get("geometry") or [{}])[-1]; co = g.get("coordinates")
            la, lo = (co[1], co[0]) if g.get("type") == "Point" else ((co[0][0][1], co[0][0][0]) if co else (None, None))
            codes = sorted({c for cat in e.get("categories", []) for c in EONET.get(cat["id"], [])})
            rec(codes, (g.get("date") or iso(NOW))[:19] + "Z", e["title"], la, lo, e.get("link"), e["id"])


# ---------- 地震目录：USGS（含崩塌、爆破、矿震类型） ----------
@source("USGS 地震目录")
def usgs():
    x = get(f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime={iso(NOW - timedelta(days=30))}&minlatitude={BOX[0]}&maxlatitude={BOX[1]}&minlongitude={BOX[2]}&maxlongitude={BOX[3]}")
    T = {"earthquake": ["GH0101"], "landslide": ["GH0300", "GH0301"], "explosion": ["TL0304"], "quarry blast": ["TL0307"], "mining explosion": ["TL0307"], "rock burst": ["TL0307"], "ice quake": ["MH0801"]}
    for f in x["features"]:
        p = f["properties"]; co = f["geometry"]["coordinates"]
        rec(T.get(p.get("type"), ["GH0101"]), iso(datetime.fromtimestamp(p["time"] / 1000, timezone.utc)), f"M{p['mag']} {p.get('type')} · {p.get('place')}", co[1], co[0], p.get("url"), "usgs-" + f["id"])
    g = get(f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime={iso(NOW - timedelta(days=7))}&minmagnitude=6")
    for f in g["features"]:
        p = f["properties"]; co = f["geometry"]["coordinates"]
        rec(["GH0101"], iso(datetime.fromtimestamp(p["time"] / 1000, timezone.utc)), f"M{p['mag']} · {p.get('place')}", co[1], co[0], p.get("url"), "usgs-" + f["id"])


# ---------- GDACS 全球灾害 ----------
@source("GDACS")
def gdacs():
    x = get(f"https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH?fromdate={(NOW - timedelta(days=60)).strftime('%Y-%m-%d')}&todate={NOW.strftime('%Y-%m-%d')}&alertlevel=green;orange;red")
    T = {"EQ": ["GH0101"], "FL": ["MH0600"], "TC": ["MH0309"], "DR": ["MH0401"], "WF": ["EN0205"], "VO": ["GH0201", "GH0202"], "TS": ["MH0705"]}
    for f in x.get("features", []):
        p = f["properties"]; co = f["geometry"]["coordinates"]
        rec(T.get(p.get("eventtype"), []), (p.get("fromdate") or iso(NOW))[:19] + "Z", f"{p.get('alertlevel')} · {p.get('name')}", co[1], co[0], (p.get("url") or {}).get("report"), f"gdacs-{p.get('eventtype')}-{p.get('eventid')}")


# ---------- 空间天气：NOAA SWPC ----------
@source("NOAA SWPC 空间天气")
def swpc():
    for a in get("https://services.swpc.noaa.gov/products/alerts.json"):
        m = a.get("message", ""); pid = a.get("product_id", "")
        codes = (["ET0101"] if re.search(r"Geomagnetic|K-index", m) else []) + (["ET0102", "ET0103"] if re.search(r"X-ray|Radio Blackout|Radio Emission", m) else []) + (["ET0104"] if re.search(r"Proton|Radiation Storm|Electron", m) else [])
        t = a.get("issue_datetime", "").replace(" ", "T")[:19] + "Z"
        rec(codes, t, re.sub(r"\s+", " ", m)[:160], url="https://www.swpc.noaa.gov/products/alerts-watches-and-warnings", rid=f"swpc-{pid}-{t}", local=True)
    for f in get("https://services.swpc.noaa.gov/json/goes/primary/xray-flares-7-day.json"):
        if (f.get("max_class") or "")[:1] in ("M", "X"):
            rec(["ET0103", "ET0102"], (f.get("max_time") or f.get("begin_time"))[:19] + "Z", f"太阳耀斑 {f.get('max_class')}", rid="flare-" + str(f.get("begin_time")), local=True)


# ---------- 近地天体、火球、空间碎片 ----------
@source("NASA CNEOS")
def cneos():
    x = get(f"https://ssd-api.jpl.nasa.gov/fireball.api?date-min={(NOW - timedelta(days=365)).strftime('%Y-%m-%d')}")
    F = x.get("fields", [])
    for row in x.get("data", []):
        d = dict(zip(F, row)); la = float(d["lat"]) * (1 if d.get("lat-dir") == "N" else -1) if d.get("lat") else None; lo = float(d["lon"]) * (1 if d.get("lon-dir") == "E" else -1) if d.get("lon") else None
        rec(["ET0201", "ET0203"], d["date"].replace(" ", "T")[:19] + "Z", f"火球 能量 {d.get('energy')}e10 J", la, lo, "https://cneos.jpl.nasa.gov/fireballs/", "fb-" + d["date"])
    y = get(f"https://ssd-api.jpl.nasa.gov/cad.api?date-min={(NOW - timedelta(days=30)).strftime('%Y-%m-%d')}&date-max={NOW.strftime('%Y-%m-%d')}&dist-max=0.01")
    F = y.get("fields", [])
    for row in y.get("data", []):
        d = dict(zip(F, row)); t = datetime.strptime(d["cd"], "%Y-%b-%d %H:%M").replace(tzinfo=timezone.utc)
        rec(["ET0205"], iso(t), f"{d['des']} 近地掠过 {float(d['dist']) * 389.17:.1f} 倍月距", None, None, "https://cneos.jpl.nasa.gov/ca/", "cad-" + d["des"] + d["cd"], local=False)


@source("CelesTrak 在轨目标")
def celestrak():
    n = 0
    for grp in ("cosmos-1408-debris", "fengyun-1c-debris", "iridium-33-debris", "cosmos-2251-debris"):
        n += len(get(f"https://celestrak.org/NORAD/elements/gp.php?GROUP={grp}&FORMAT=json"))
    new = get("https://celestrak.org/NORAD/elements/gp.php?GROUP=last-30-days&FORMAT=json")
    for o in new:
        rec(["ET0204"], (o.get("EPOCH") or iso(NOW))[:19] + "Z", f"新入轨 {o.get('OBJECT_NAME')}", rid="ct-" + str(o.get("NORAD_CAT_ID")))
    rec(["ET0206"], iso(NOW), f"跟踪中的碎片（四次大型解体事件）{n} 个", rid="ct-debris-" + NOW.strftime("%Y%m%d%H"))


# ---------- 疫情：WHO、FluNet ----------
DIS = {"BI0201": "anthrax", "BI0202": "brucell", "BI0203": "chikungunya", "BI0204": "cholera", "BI0205": "covid|sars-cov-2", "BI0206": "crimean-congo", "BI0207": "dengue",
       "BI0208": "diphtheria", "BI0209": "ebola", "BI0210": "e\\. coli|escherichia", "BI0211": "hepatitis a", "BI0212": "hepatitis b", "BI0213": "hepatitis c", "BI0215": "lassa",
       "BI0217": "leptospir", "BI0218": "listeri", "BI0219": "malaria", "BI0220": "marburg", "BI0221": "measles", "BI0222": "meningo", "BI0223": "mers", "BI0224": "mpox",
       "BI0226": "typhoid", "BI0227": "pertussis", "BI0228": "plague", "BI0229": "polio", "BI0231": "q fever", "BI0232": "rabies", "BI0236": "\\bsars\\b", "BI0240": "west nile",
       "BI0241": "yellow fever", "BI0242": "zika", "BI0244": "pandemic influenza|novel influenza", "BI0245": "avian influenza|h5n1|h7n9|h9n2", "BI0109": "haemorrhagic|hemorrhagic",
       "BI0302": "african swine", "BI0306": "foot and mouth", "BI0311": "rift valley", "BI0230": "prion|creutzfeldt", "BI0216": "leprosy", "BI0237": "tubercul", "BI0108": "vector", "BI0113": "zoonotic"}


@source("WHO 疫情通报")
def who():
    x = get("https://www.who.int/api/news/diseaseoutbreaknews?sf_culture=en&$orderby=PublicationDateAndTime%20desc&$top=100")
    for r in x.get("value", []):
        t = (r.get("PublicationDateAndTime") or "")[:19] + "Z"; title = r.get("Title") or ""
        codes = [c for c, pat in DIS.items() if re.search(pat, title, re.I)]
        rec(codes or ["BI0101"], t, title, None, None, "https://www.who.int/emergencies/disease-outbreak-news/item/" + (r.get("UrlName") or ""), "who-" + (r.get("UrlName") or t),
            local=bool(re.search(r"Nepal|China|India|Bhutan|Bangladesh|Pakistan", title)))


@source("WHO FluNet（尼泊尔）")
def flunet():
    x = get("https://xmart-api-public.who.int/FLUMART/VIW_FNT?$filter=COUNTRY_CODE%20eq%20%27NPL%27&$orderby=ISO_WEEKSTARTDATE%20desc&$top=8")
    for r in x.get("value", []):
        pos = r.get("INF_ALL") or 0; tot = r.get("SPEC_PROCESSED_NB") or 0
        codes = ["BI0243", "BI0101"] + (["BI0245"] if r.get("AH5") else [])
        rec(codes, r["ISO_WEEKSTARTDATE"][:10] + "T00:00:00Z", f"尼泊尔流感监测第 {r.get('ISO_WEEK')} 周：检测 {tot} 份，阳性 {pos}", 27.7, 85.3, "https://www.who.int/tools/flunet", f"flunet-{r.get('ISO_YEAR')}-{r.get('ISO_WEEK')}-{r.get('ORIGIN_SOURCE')}")


@source("WOAH WAHIS 动物疫情")
def wahis():
    body = json.dumps({"pageNumber": 1, "pageSize": 50, "searchText": "", "sortColumn": "startDate", "sortOrder": "desc", "eventStatuses": [], "reportTypes": [], "countries": [], "firstDiseases": [], "secondDiseases": [], "typeStatuses": [], "reasons": [], "eventStartDate": None}).encode()
    x = get("https://wahis.woah.org/api/v1/pi/event/filtered-list?language=en", data=body, headers={"content-type": "application/json", "accept": "application/json", "env": "PRD", "accept-language": "en"})
    L = x.get("list") or x.get("events") or x.get("content") or []
    for e in L:
        name = e.get("disease") or e.get("diseaseName") or ""; ctry = e.get("country") or e.get("countryName") or ""
        codes = [c for c, pat in DIS.items() if re.search(pat, name, re.I)] or ["BI0301"]
        rec(codes, (e.get("startDate") or e.get("eventStartDate") or iso(NOW))[:19] + "Z", f"{ctry} · {name}", None, None, "https://wahis.woah.org/", "wahis-" + str(e.get("eventId") or e.get("id")),
            local=bool(re.search(r"Nepal|China|India|Bhutan", ctry)))


# ---------- 食品药品召回（美国 FDA，公开） ----------
@source("openFDA 食品药品召回")
def openfda():
    for kind, codes in (("food", ["CH0601", "BI0104"]), ("drug", ["CH0602"])):
        for r in get(f"https://api.fda.gov/{kind}/enforcement.json?sort=report_date:desc&limit=50").get("results", []):
            reason = r.get("reason_for_recall", ""); cs = list(codes)
            if re.search(r"listeria", reason, re.I): cs.append("BI0218")
            if re.search(r"salmonella|e\. ?coli", reason, re.I): cs.append("BI0210")
            if re.search(r"lead\b", reason, re.I): cs.append("CH0103")
            if re.search(r"aflatoxin", reason, re.I): cs.append("CH0201")
            if re.search(r"methanol", reason, re.I): cs.append("CH0603")
            d = r.get("report_date", "")
            rec(cs, f"{d[:4]}-{d[4:6]}-{d[6:8]}T00:00:00Z", f"{r.get('recalling_firm')}：{reason[:120]}", None, None, None, "fda-" + r.get("recall_number", ""))


# ---------- 网络安全 ----------
@source("CISA 已利用漏洞")
def cisa():
    x = get("https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json")
    for v in x.get("vulnerabilities", []):
        if v.get("dateAdded", "") >= (NOW - timedelta(days=30)).strftime("%Y-%m-%d"):
            cs = ["TL0101", "TL0103"] + (["TL0105"] if re.search(r"supply", v.get("shortDescription", ""), re.I) else [])
            rec(cs, v["dateAdded"] + "T00:00:00Z", f"{v.get('vendorProject')} {v.get('product')}：{v.get('vulnerabilityName')}", None, None, "https://www.cisa.gov/known-exploited-vulnerabilities-catalog", "kev-" + v["cveID"])


@source("Have I Been Pwned 数据泄露")
def hibp():
    for b in get("https://haveibeenpwned.com/api/v3/breaches"):
        if (b.get("AddedDate") or "") >= iso(NOW - timedelta(days=30)):
            rec(["TL0102"], b["AddedDate"][:19] + "Z", f"{b.get('Title')} 泄露 {b.get('PwnCount')} 个账号", None, None, "https://haveibeenpwned.com/PwnedWebsites", "hibp-" + b["Name"])


@source("Cloudflare Radar", need="CF_RADAR_TOKEN")
def cfradar():
    H = {"authorization": "Bearer " + os.environ["CF_RADAR_TOKEN"]}
    for path, cs in (("annotations/outages", ["TL0211", "TL0212", "TL0209"]), ("attacks/layer3/top/locations/target", ["TL0104"])):
        x = get(f"https://api.cloudflare.com/client/v4/radar/{path}?location=NP&dateRange=7d&format=json", headers=H)
        for o in (x.get("result") or {}).get("annotations", []):
            rec(cs, (o.get("startDate") or iso(NOW))[:19] + "Z", o.get("description") or "尼泊尔网络中断", 27.7, 85.3, None, "cf-" + str(o.get("id")))


@source("IODA 网络连通")
def ioda():
    a, b = int((NOW - timedelta(days=7)).timestamp()), int(NOW.timestamp())
    x = get(f"https://api.ioda.inetintel.cc.gatech.edu/v2/outages/events?from={a}&until={b}&entityType=country&entityCode=NP&format=codf")
    L = x.get("data") or []
    for e in L:
        rec(["TL0211", "TL0212"], iso(datetime.fromtimestamp(e.get("start") or e.get("from") or b, timezone.utc)), f"尼泊尔网络中断 {e.get('datasource', '')} 得分 {e.get('score', '')}", 27.7, 85.3, "https://ioda.inetintel.cc.gatech.edu/country/NP", "ioda-" + str(e.get("start")))


# ---------- 金融冲击：尼泊尔央行汇率 ----------
@source("尼泊尔央行汇率")
def nrb():
    x = get(f"https://www.nrb.org.np/api/forex/v1/rates?from={(NOW - timedelta(days=15)).strftime('%Y-%m-%d')}&to={NOW.strftime('%Y-%m-%d')}&per_page=30&page=1")
    P_ = x["data"]["payload"]; usd = []
    for d in P_:
        for r in d["rates"]:
            if r["currency"]["iso3"] == "USD": usd.append((d["date"], float(r["sell"])))
    usd.sort()
    if len(usd) >= 2:
        ch = (usd[-1][1] - usd[0][1]) / usd[0][1] * 100
        if abs(ch) >= 2: rec(["SO0401"], usd[-1][0] + "T00:00:00Z", f"尼泊尔卢比兑美元 {len(usd)} 天变化 {ch:+.1f}%", 27.7, 85.3, "https://www.nrb.org.np/forex/", "nrb-" + usd[-1][0])
    return {"usd_latest": usd[-1] if usd else None}


# ---------- 辐射：Safecast ----------
@source("Safecast 辐射")
def safecast():
    x = get(f"https://api.safecast.org/measurements.json?latitude=27.7&longitude=85.3&distance=500000&captured_after={(NOW - timedelta(days=365)).strftime('%Y-%m-%d')}&per_page=100")
    hi = [m for m in x if (m.get("value") or 0) > 300 and m.get("unit") == "cpm"]
    for m in hi:
        rec(["TL0602"], m["captured_at"][:19] + "Z", f"辐射读数 {m['value']} cpm", m.get("latitude"), m.get("longitude"), "https://map.safecast.org/", "sc-" + str(m["id"]))
    return {"measurements_1y": len(x)}


# ---------- 卫星大气成分：Sentinel-5P（微软 Planetary Computer） ----------
S5P = {"L2__NO2___": ["EN0103", "EN0102", "TL0302"], "L2__SO2___": ["GH0205", "EN0105", "TL0302"], "L2__CO____": ["CH0302", "MH0205", "EN0103"], "L2__CH4___": ["GH0407"],
       "L2__AER_AI": ["MH0201", "MH0203", "MH0205", "EN0104"], "L2__HCHO__": ["EN0103"], "L2__O3____": ["ET0202"]}


@source("Sentinel-5P 大气成分")
def s5p():
    body = {"collections": ["sentinel-5p-l2-netcdf"], "bbox": [BOX[2], BOX[0], BOX[3], BOX[1]], "datetime": f"{iso(NOW - timedelta(days=2))}/{iso(NOW)}", "limit": 200}
    x = get("https://planetarycomputer.microsoft.com/api/stac/v1/search", data=json.dumps(body).encode(), headers={"content-type": "application/json"})
    got = {}
    for f in x.get("features", []):
        pt = f["properties"].get("s5p:product_type") or f["id"].split("_20")[0].replace("S5P_L2_", "L2__")
        key = next((k for k in S5P if k.strip("_") in pt.replace("_", "") or k == pt), None)
        if key and key not in got:
            got[key] = f["properties"]["datetime"][:19] + "Z"
    for k, t in got.items():
        rec(S5P[k], t, f"Sentinel-5P {k.strip('_').replace('L2', '')} 覆盖喜马拉雅（有观测，未计算数值）", 28.0, 86.0, "https://planetarycomputer.microsoft.com/dataset/sentinel-5p-l2-netcdf", f"s5p-{k}-{t}", observation=True)
    return {"products": sorted(got)}


# ---------- 海洋与海啸 ----------
@source("太平洋海啸预警中心")
def ptwc():
    import xml.etree.ElementTree as ET
    for feed in ("https://www.tsunami.gov/events/xml/PHEBAtom.xml", "https://www.tsunami.gov/events/xml/PAAQAtom.xml"):
        root = ET.fromstring(get(feed, raw=True)); ns = {"a": "http://www.w3.org/2005/Atom"}
        for e in root.findall("a:entry", ns):
            rec(["MH0705"], e.findtext("a:updated", namespaces=ns)[:19] + "Z", re.sub(r"\s+", " ", e.findtext("a:title", namespaces=ns) or ""), None, None, "https://www.tsunami.gov/", "ptwc-" + (e.findtext("a:id", namespaces=ns) or ""))


@source("NOAA NCEI 历史灾害库")
def ncei():
    for kind, cs in (("tsunamis/events", ["MH0705"]), ("volcanoes", ["GH0201", "GH0202"])):
        for e in get(f"https://www.ngdc.noaa.gov/hazel/hazard-service/api/v1/{kind}?minYear={NOW.year - 1}").get("items", []):
            t = f"{e.get('year')}-{(e.get('month') or 1):02d}-{(e.get('day') or 1):02d}T00:00:00Z"
            rec(cs, t, f"{e.get('country', '')} {e.get('locationName') or e.get('name') or ''}", e.get("latitude"), e.get("longitude"), "https://www.ngdc.noaa.gov/hazel/", f"ncei-{kind}-{e.get('id')}")


@source("IOC 海平面站")
def ioc():
    x = get("https://www.ioc-sealevelmonitoring.org/service.php?query=stationlist&showall=all", timeout=90)
    on = [s for s in x if (s.get("lasttime") or s.get("Lasttime") or "") >= (NOW - timedelta(hours=6)).strftime("%Y-%m-%d %H")]
    rec(["MH0703", "MH0704", "MH0701", "MH0702", "MH0601", "MH0602", "EN0402"], iso(NOW), f"全球 {len(x)} 个潮位站，最近 6 小时在报 {len(on)} 个", None, None, "https://www.ioc-sealevelmonitoring.org/", "ioc-" + NOW.strftime("%Y%m%d%H"))
    return {"stations": len(x), "reporting_6h": len(on)}


@source("IBTrACS 活跃气旋")
def ibtracs():
    txt = get("https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-ibtracs/v04r01/access/csv/ibtracs.ACTIVE.list.v04r01.csv", raw=True).decode()
    rows = list(csv.DictReader(io.StringIO(txt)))[1:]; last = {}
    for r in rows: last[r["SID"]] = r
    for sid, r in last.items():
        nat = r.get("NATURE", ""); cs = ["MH0309"] if nat == "TS" else ["MH0307"] if nat == "ET" else ["MH0308"] if nat == "SS" else ["MH0306"]
        try: la, lo = float(r["LAT"]), float(r["LON"])
        except Exception: la = lo = None
        rec(cs, r["ISO_TIME"].replace(" ", "T") + "Z", f"{r.get('NAME')} ({r.get('BASIN')}) 风速 {r.get('WMO_WIND') or r.get('USA_WIND')}", la, lo, "https://www.ncei.noaa.gov/products/international-best-track-archive", "ib-" + sid)


@source("NSIDC 海冰")
def nsidc():
    for hemi, u in (("北极", "https://noaadata.apps.nsidc.org/NOAA/G02135/north/daily/data/N_seaice_extent_daily_v4.0.csv"), ("南极", "https://noaadata.apps.nsidc.org/NOAA/G02135/south/daily/data/S_seaice_extent_daily_v4.0.csv")):
        rows = [l.split(",") for l in get(u, raw=True).decode().splitlines()[2:] if l.strip()]
        y, m, d, ext = rows[-1][0].strip(), rows[-1][1].strip(), rows[-1][2].strip(), rows[-1][3].strip()
        rec(["MH0706", "MH0707"], f"{y}-{int(m):02d}-{int(d):02d}T00:00:00Z", f"{hemi}海冰范围 {ext} 百万平方公里", None, None, "https://nsidc.org/data/seaice_index", f"nsidc-{hemi}-{y}{m}{d}", observation=True)


@source("史密森尼火山周报")
def gvp():
    import xml.etree.ElementTree as ET
    b = get("https://volcano.si.edu/news/WeeklyVolcanoRSS.xml", raw=True, headers={"user-agent": "Mozilla/5.0 (compatible; everest-hazard-scan)"})
    for it in ET.fromstring(b).iter("item"):
        rec(["GH0201", "GH0202", "GH0205"], iso(NOW), it.findtext("title") or "", None, None, it.findtext("link"), "gvp-" + (it.findtext("guid") or it.findtext("title") or ""))


# ---------- 生物多样性、森林 ----------
@source("GBIF 物种记录（尼泊尔）")
def gbif():
    x = get(f"https://api.gbif.org/v1/occurrence/search?country=NP&eventDate={(NOW - timedelta(days=30)).strftime('%Y-%m-%d')},{NOW.strftime('%Y-%m-%d')}&limit=0&facet=establishmentMeans")
    rec(["EN0501"], iso(NOW), f"尼泊尔近 30 天 {x.get('count')} 条物种观测记录", 28.0, 84.0, "https://www.gbif.org/country/NP/summary", "gbif-" + NOW.strftime("%Y%m%d"), observation=True)
    y = get(f"https://api.gbif.org/v1/occurrence/search?country=NP&establishmentMeans=INTRODUCED&eventDate={(NOW - timedelta(days=365)).strftime('%Y-%m-%d')},{NOW.strftime('%Y-%m-%d')}&limit=0")
    rec(["BI0403", "EN0204"], iso(NOW), f"尼泊尔近一年外来物种记录 {y.get('count')} 条", 28.0, 84.0, "https://www.gbif.org/", "gbif-intro-" + NOW.strftime("%Y%m%d"), observation=True)


@source("Global Forest Watch", need="GFW_API_KEY")
def gfw():
    sql = urllib.parse.quote(f"SELECT COUNT(*) FROM results WHERE gfw_integrated_alerts__date >= '{(NOW - timedelta(days=30)).strftime('%Y-%m-%d')}'")
    x = get(f"https://data-api.globalforestwatch.org/dataset/gfw_integrated_alerts/latest/query?sql={sql}&geostore_origin=rw&geostore_id=nepal", headers={"x-api-key": os.environ["GFW_API_KEY"]})
    rec(["EN0201", "EN0203"], iso(NOW), f"尼泊尔近 30 天林地扰动预警 {json.dumps(x.get('data'))[:60]}", 28.0, 84.0, "https://www.globalforestwatch.org/", "gfw-" + NOW.strftime("%Y%m%d"))


@source("NASA FIRMS 火点", need="FIRMS_MAP_KEY")
def firms():
    txt = get(f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{os.environ['FIRMS_MAP_KEY']}/VIIRS_SNPP_NRT/{BOX[2]},{BOX[0]},{BOX[3]},{BOX[1]}/2", raw=True).decode()
    for r in list(csv.DictReader(io.StringIO(txt)))[:300]:
        rec(["EN0205", "TL0305", "MH0205"], f"{r['acq_date']}T{r['acq_time'].zfill(4)[:2]}:{r['acq_time'].zfill(4)[2:]}:00Z", f"卫星火点 FRP {r.get('frp')}", float(r["latitude"]), float(r["longitude"]), "https://firms.modaps.eosdis.nasa.gov/", f"firms-{r['latitude']}-{r['longitude']}-{r['acq_date']}{r['acq_time']}")


@source("OpenAQ 空气质量", need="OPENAQ_API_KEY")
def openaq():
    x = get("https://api.openaq.org/v3/locations?countries_id=126&limit=100", headers={"x-api-key": os.environ["OPENAQ_API_KEY"]})
    rec(["EN0103"], iso(NOW), f"尼泊尔 {len(x.get('results', []))} 个空气质量站", 27.7, 85.3, "https://openaq.org/", "openaq-" + NOW.strftime("%Y%m%d%H"), observation=True)


@source("ACLED 冲突事件", need="ACLED_KEY")
def acled():
    k = os.environ["ACLED_KEY"].split(":")
    x = get(f"https://api.acleddata.com/acled/read?key={k[0]}&email={k[1] if len(k) > 1 else ''}&country=Nepal&event_date={(NOW - timedelta(days=30)).strftime('%Y-%m-%d')}|{NOW.strftime('%Y-%m-%d')}&event_date_where=BETWEEN&limit=200")
    T = {"Battles": ["SO0102"], "Violence against civilians": ["SO0301"], "Protests": ["SO0103"], "Riots": ["SO0103"], "Explosions/Remote violence": ["SO0201", "TL0304"]}
    for e in x.get("data", []):
        rec(T.get(e.get("event_type"), ["SO0103"]), e["event_date"] + "T00:00:00Z", f"{e.get('event_type')} · {e.get('location')}", float(e["latitude"]), float(e["longitude"]), "https://acleddata.com/", "acled-" + e["event_id_cnty"])


@source("ReliefWeb", need="RELIEFWEB_APPNAME")
def reliefweb():
    x = get(f"https://api.reliefweb.int/v2/disasters?appname={urllib.parse.quote(os.environ['RELIEFWEB_APPNAME'])}&filter[field]=country&filter[value]=Nepal&sort[]=date.created:desc&limit=20&fields[include][]=name&fields[include][]=date.created&fields[include][]=url&fields[include][]=type.name")
    for d in x.get("data", []):
        f = d["fields"]; rec([], f["date"]["created"][:19] + "Z", f["name"], 28.0, 84.0, f.get("url"), "rw-" + str(d["id"]))


# ---------- 新闻：GDELT，每种灾害一个关键词，按批 OR 查询，限定喜马拉雅 ----------
def kw_of(h):
    over = {"MH0102": "lightning", "MH0201": "dust storm", "MH0306": "cyclone", "MH0503": "dzud", "MH0600": "flood", "MH0607": "glacial lake outburst", "MH0801": "avalanche",
            "GH0101": "earthquake", "GH0300": "landslide", "GH0301": "rockfall", "GH0303": "debris flow", "EN0205": "forest fire", "TL0205": "dam collapse", "TL0209": "blackout",
            "TL0405": "road accident", "TL0401": "plane crash", "TL0402": "boat capsize", "SO0302": "stampede", "SO0103": "protest", "BI0605": "snakebite", "BI0604": "wildlife attack",
            "CH0302": "carbon monoxide", "TL0104": "DDoS", "TL0102": "data breach", "TL0101": "malware", "SO0401": "financial crisis", "TL0204": "bridge collapse", "TL0201": "building collapse"}
    if h["code"] in over: return over[h["code"]]
    k = re.sub(r"\(.*?\)", "", h["label"]).split("/")[0].split(",")[0].strip().lower()
    k = re.sub(r"\b(human|animal|and|including|other)\b", "", k).strip()
    return k if len(k) >= 4 else h["label"].lower()


@source("GDELT 新闻")
def gdelt():
    KW = {h["code"]: kw_of(h) for h in HIPS}
    items = list(KW.items()); n_q = 0; arts_all = []
    for i in range(0, len(items), 10):
        grp = items[i:i + 10]
        terms = " OR ".join(f'"{k}"' if " " in k else k for _, k in grp)
        q = f"({terms}) (Nepal OR Himalaya OR Everest OR Tibet) sourcelang:english"
        u = "https://api.gdeltproject.org/api/v2/doc/doc?" + urllib.parse.urlencode({"query": q, "mode": "artlist", "maxrecords": 250, "format": "json", "timespan": "7d"})
        for wait in (7, 30, 90):
            time.sleep(wait)
            try:
                raw = get(u, raw=True, timeout=60); break
            except Exception as e:
                if "429" not in str(e) or wait == 90: raise
        n_q += 1
        arts = json.loads(raw).get("articles", []) if raw.strip().startswith(b"{") else []
        for a in arts:
            title = a.get("title", "")
            codes = [c for c, k in grp if re.search(r"\b" + re.escape(k) + r"\b", title, re.I)]
            if not codes: continue
            t = datetime.strptime(a["seendate"], "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
            rec(codes, iso(t), f"{a.get('domain')}：{title}", None, None, a.get("url"), "gdelt-" + a.get("url", "")[:200], local=True, news=True)
    return {"queries": n_q}


# ---------- 运行 ----------
for s in SOURCES:
    s()

# 记录合并进 90 天的累积库
prev = []
try:
    prev = json.load(open(f"{OUT}/records.json")).get("records", [])
except Exception:
    import subprocess
    try:
        prev = json.loads(subprocess.check_output(["git", "show", "origin/events:hazards/records.json"], stderr=subprocess.DEVNULL)).get("records", [])
    except Exception:
        prev = []
byid = {r.get("id") or (r["src"] + r["t"] + r["title"]): r for r in prev if r.get("t", "") >= iso(NOW - timedelta(days=90))}
for r in RECS: byid[r.get("id") or (r["src"] + r["t"] + r["title"])] = r
allrec = sorted(byid.values(), key=lambda r: r["t"], reverse=True)

# 每种灾害：哪些来源对应、实测结果、状态
SRC_OF = {}
for r in allrec:
    for c in r.get("codes", []): SRC_OF.setdefault(c, set()).add(r["src"])
# 没有记录的灾害，也列出“理论上覆盖它”的来源（GDELT 覆盖全部；其余见映射表）
STATIC = {}
for k, cs in BIPAD_HZ.items():
    for c in cs: STATIC.setdefault(c, set()).add("BIPAD 灾害事件库")
for cs in EONET.values():
    for c in cs: STATIC.setdefault(c, set()).add("NASA EONET")
for c in DIS: STATIC.setdefault(c, set()).add("WHO 疫情通报")
for cs in S5P.values():
    for c in cs: STATIC.setdefault(c, set()).add("Sentinel-5P 大气成分")
for c in ("ET0101", "ET0102", "ET0103", "ET0104"): STATIC.setdefault(c, set()).add("NOAA SWPC 空间天气")
for c in ("ET0201", "ET0203", "ET0205"): STATIC.setdefault(c, set()).add("NASA CNEOS")
for c in ("ET0204", "ET0206"): STATIC.setdefault(c, set()).add("CelesTrak 在轨目标")
for c in ("TL0101", "TL0103", "TL0105"): STATIC.setdefault(c, set()).add("CISA 已利用漏洞")
for c in ("TL0102",): STATIC.setdefault(c, set()).add("Have I Been Pwned 数据泄露")
for c in ("TL0104", "TL0209", "TL0211", "TL0212"): STATIC.setdefault(c, set()).add("Cloudflare Radar")
for c in ("TL0211", "TL0212"): STATIC.setdefault(c, set()).add("IODA 网络连通")
for c in ("SO0401",): STATIC.setdefault(c, set()).add("尼泊尔央行汇率")
for c in ("TL0601", "TL0602", "TL0603"): STATIC.setdefault(c, set()).add("Safecast 辐射")
for c in ("MH0705",): STATIC.setdefault(c, set()).update({"太平洋海啸预警中心", "NOAA NCEI 历史灾害库"})
for c in ("MH0701", "MH0702", "MH0703", "MH0704", "MH0601", "MH0602", "EN0402"): STATIC.setdefault(c, set()).add("IOC 海平面站")
for c in ("MH0306", "MH0307", "MH0308", "MH0309"): STATIC.setdefault(c, set()).add("IBTrACS 活跃气旋")
for c in ("MH0706", "MH0707"): STATIC.setdefault(c, set()).add("NSIDC 海冰")
for c in ("GH0201", "GH0202", "GH0203", "GH0204", "GH0205"): STATIC.setdefault(c, set()).update({"史密森尼火山周报", "NOAA NCEI 历史灾害库"})
for c in ("EN0501", "BI0403", "EN0204"): STATIC.setdefault(c, set()).add("GBIF 物种记录（尼泊尔）")
for c in ("EN0201", "EN0203"): STATIC.setdefault(c, set()).add("Global Forest Watch")
for c in ("EN0205", "TL0305", "MH0205"): STATIC.setdefault(c, set()).add("NASA FIRMS 火点")
for c in ("EN0103",): STATIC.setdefault(c, set()).update({"OpenAQ 空气质量", "BIPAD 空气质量站"})
for c in ("SO0101", "SO0102", "SO0103", "SO0201", "SO0301"): STATIC.setdefault(c, set()).add("ACLED 冲突事件")
for c in ("CH0601", "CH0602", "BI0104", "BI0218", "BI0210", "CH0103", "CH0201", "CH0603"): STATIC.setdefault(c, set()).add("openFDA 食品药品召回")
for c in ("BI0243", "BI0101", "BI0245"): STATIC.setdefault(c, set()).add("WHO FluNet（尼泊尔）")
for c in ("BI0301", "BI0302", "BI0303", "BI0304", "BI0305", "BI0306", "BI0307", "BI0308", "BI0309", "BI0310", "BI0311", "BI0312", "BI0313", "BI0314", "BI0245", "BI0201", "BI0232"):
    STATIC.setdefault(c, set()).add("WOAH WAHIS 动物疫情")
for c in ("GH0101", "GH0300", "GH0301", "TL0304", "TL0307"): STATIC.setdefault(c, set()).add("USGS 地震目录")
for c in ("GH0101", "MH0600", "MH0309", "MH0401", "EN0205", "GH0201", "MH0705"): STATIC.setdefault(c, set()).add("GDACS")
for h in HIPS: STATIC.setdefault(h["code"], set()).add("GDELT 新闻")

hz = []
for h in HIPS:
    c = h["code"]; srcs = sorted(STATIC.get(c, set()) | SRC_OF.get(c, set()))
    mine = [r for r in allrec if c in r.get("codes", [])]
    loc = [r for r in mine if r.get("local")]
    tested = [s for s in srcs if RES.get(s, {}).get("state") == "ok"]
    state = ("local" if loc else "global" if mine else "ok_none" if tested else "key" if any(RES.get(s, {}).get("state") == "key" for s in srcs) else "fail")
    hz.append({"code": c, "label": h["label"], "label_zh": h["label_zh"], "family": h["family"], "family_zh": h["family_zh"], "sources": srcs,
               "tested_ok": tested, "n_90d": len(mine), "n_local_90d": len(loc), "latest": mine[0]["t"] if mine else None,
               "latest_title": (loc or mine)[0]["title"] if mine else None, "state": state})

# 事件候选：喜马拉雅高山区的自然灾害（BIPAD 事件库、EONET），或尼泊尔造成 3 人以上死亡的事件
MOUNTAIN = (27.3, 31.5, 80.0, 88.3)
cand = []
for r in allrec:
    if r["t"] < iso(NOW - timedelta(days=30)): continue
    nat = any(c[:2] in ("MH", "GH", "EN") for c in r.get("codes", []))
    mtn = r.get("lat") and MOUNTAIN[0] <= r["lat"] <= MOUNTAIN[1] and MOUNTAIN[2] <= r["lon"] <= MOUNTAIN[3]
    if r["src"] in ("BIPAD 灾害事件库",) and ((nat and mtn and r["lat"] >= 27.6) or (r.get("deaths") or 0) >= 3):
        cand.append({"id": "hz-" + r["id"], "kind": r.get("hazard_name") or "", "hips": r["codes"], "title": r["title"], "title_en": r["title"], "place": r["title"].split(" at ")[-1],
                     "lat": r["lat"], "lon": r["lon"], "t": r["t"], "first_seen": iso(NOW),
                     "src": [{"k": r["id"], "t": r["t"], "src": "BIPAD 灾害事件库", "text": f"{r['title']}（死亡 {r.get('deaths', 0)}、受伤 {r.get('injured', 0)}、失踪 {r.get('missing', 0)}）",
                              "text_en": f"{r['title']} (dead {r.get('deaths', 0)}, injured {r.get('injured', 0)}, missing {r.get('missing', 0)})", "url": r.get("url")}]})

from collections import Counter
summary = {"updated": iso(NOW), "sources": RES, "by_state": Counter(h["state"] for h in hz),
           "by_family": {f: Counter(h["state"] for h in hz if h["family_zh"] == f) for f in dict.fromkeys(h["family_zh"] for h in hz)}}
json.dump({**summary, "hazards": hz}, open(f"{OUT}/scan.json", "w"), ensure_ascii=False, indent=1)
json.dump({"updated": iso(NOW), "records": allrec[:20000]}, open(f"{OUT}/records.json", "w"), ensure_ascii=False)
json.dump({"updated": iso(NOW), "events": cand}, open(f"{OUT}/scan_events.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps(summary["by_state"]), len(allrec), "records", len(cand), "candidates")
