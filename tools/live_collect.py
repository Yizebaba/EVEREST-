#!/usr/bin/env python3
"""珠峰实时采集（每 10 分钟由 GitHub Actions 运行）。只读外部公开接口，结果写进 state/ 目录：
  levels.json  BIPAD/尼泊尔水文局遥测水位：{seriesId: {"meta":{...}, "obs":[[ISO时间, 水位m], ...]}}，保留 14 天
  seis.json    IO.EVN 垂直向每分钟振幅（去均值后的均方根和最大绝对值，单位：计数，未做仪器响应校正），保留 3 天
  quakes.json  USGS 范围内地震（含被标为 landslide 的崩塌事件），近 60 天
  alerts.json  BIPAD 警报最近 30 条
  runs.json    每次采集的时间与各源状态（用来证明是否在实时更新），保留 3 天
不做任何判断或预测；停报就记停报，不补值。"""
import json, os, sys, datetime as dt, urllib.request, traceback

NOW = dt.datetime.now(dt.timezone.utc)
ST = sys.argv[1] if len(sys.argv) > 1 else "state"
os.makedirs(ST, exist_ok=True)
BBOX = (84.5, 26.3, 89.0, 29.8)  # 西 南 东 北
# 珠峰、Rolwaling、阿伦、博特科西、科西干流的关键站（BIPAD stationSeriesId）
SERIES = {5385: "Imja 冰湖出口", 5378: "Imja 湖下游（疑似故障）", 12378: "Imja 河 Dingboche", 5287: "Imja 河 Pangboche",
          1867: "Tsho Rolpa 冰湖出口", 1877: "Rolwaling 河 Bedding", 1500: "杜德科西 Rabuwabazar", 26631: "杜德科西 Jayaramghat",
          23263: "阿伦河 Kimathanka", 2874: "阿伦河 Uwa Gau", 21089: "Barun 河 Syaksila", 1481: "阿伦河 Turkeghat",
          22609: "博特科西 Kodari", 1640: "博特科西 Bahrabise", 1508: "萨普塔科西 Chatara"}

def get(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": "everest-live/0.1 (github.com/Yizebaba/everest-insar-pipeline)"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def load(name, default):
    p = os.path.join(ST, name)
    try:
        return json.load(open(p))
    except Exception:
        return default

def save(name, obj):
    json.dump(obj, open(os.path.join(ST, name), "w"), ensure_ascii=False, separators=(",", ":"))

def iso(t):
    return t.astimezone(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

run = {"t": iso(NOW), "src": {}}

# 1 水位
try:
    levels = load("levels.json", {})
    seen = 0
    for off in range(0, 600, 100):
        rows = json.loads(get(f"https://bipadportal.gov.np/api/v1/river-stations/?format=json&limit=100&offset={off}")).get("results", [])
        if not rows:
            break
        for r in rows:
            sid = r.get("stationSeriesId")
            if sid not in SERIES:
                continue
            seen += 1
            k = str(sid)
            d = levels.setdefault(k, {"meta": {}, "obs": []})
            pt = (r.get("point") or {}).get("coordinates") or [None, None]
            d["meta"] = {"name": SERIES[sid], "title": r.get("title"), "lon": pt[0], "lat": pt[1], "warning": r.get("warningLevel"),
                         "danger": r.get("dangerLevel"), "status": r.get("status"), "basin": r.get("basin"), "last_on": r.get("waterLevelOn")}
            t, v = r.get("waterLevelOn"), r.get("waterLevel")
            if t and v is not None:
                tu = iso(dt.datetime.fromisoformat(t))
                if not d["obs"] or d["obs"][-1][0] != tu:
                    d["obs"].append([tu, round(float(v), 3)])
            cut = iso(NOW - dt.timedelta(days=14))
            d["obs"] = [o for o in d["obs"] if o[0] >= cut]
    save("levels.json", levels)
    newest = max((d["meta"].get("last_on") or "" for d in levels.values()), default="")
    run["src"]["levels"] = {"ok": True, "stations": seen, "newest": newest}
except Exception as e:
    run["src"]["levels"] = {"ok": False, "err": repr(e)[:200]}

# 2 IO.EVN 每分钟振幅
try:
    import numpy as np
    from obspy.clients.fdsn import Client
    from obspy import UTCDateTime
    seis = load("seis.json", {"meta": {}, "rows": []})
    t1 = UTCDateTime(NOW); t0 = t1 - 75 * 60
    st = Client("GEOFON").get_waveforms("IO", "EVN", "*", "HHZ", t0, t1)
    st.merge(method=1, fill_value=None)
    tr = st[0]
    data = np.ma.masked_invalid(np.ma.asarray(tr.data, dtype=float))
    sr = tr.stats.sampling_rate
    start = tr.stats.starttime
    m0 = UTCDateTime(start.year, start.month, start.day, start.hour, start.minute) + 60
    have = {r[0] for r in seis["rows"]}
    while m0 + 60 <= tr.stats.endtime:
        i0 = int(round((m0 - start) * sr)); i1 = int(round((m0 + 60 - start) * sr))
        seg = data[i0:i1]
        key = m0.datetime.replace(tzinfo=dt.timezone.utc)
        k = iso(key)
        if k not in have and seg.count() > 0.9 * 60 * sr:
            x = seg.compressed(); x = x - x.mean()
            seis["rows"].append([k, round(float(np.sqrt((x * x).mean())), 1), round(float(abs(x).max()), 1)])
        m0 += 60
    seis["rows"].sort(key=lambda r: r[0])
    cut = iso(NOW - dt.timedelta(days=3))
    seis["rows"] = [r for r in seis["rows"] if r[0] >= cut]
    seis["meta"] = {"station": "IO.EVN.HHZ", "lat": 27.95865, "lon": 86.811651, "elev": 5010, "last_sample": iso(tr.stats.endtime.datetime.replace(tzinfo=dt.timezone.utc)), "unit": "counts（未做仪器响应校正）"}
    save("seis.json", seis)
    run["src"]["seis"] = {"ok": True, "newest": seis["meta"]["last_sample"], "minutes": len(seis["rows"])}
except Exception as e:
    run["src"]["seis"] = {"ok": False, "err": repr(e)[:200]}

# 3 USGS 范围内地震（含 landslide 类型）
try:
    w, s, e_, n = BBOX
    url = ("https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&orderby=time&eventtype=*"
           f"&minlatitude={s}&maxlatitude={n}&minlongitude={w}&maxlongitude={e_}&starttime={(NOW - dt.timedelta(days=60)).date()}")
    j = json.loads(get(url))
    q = [{"id": f["id"], "t": iso(dt.datetime.fromtimestamp(f["properties"]["time"] / 1000, dt.timezone.utc)), "mag": f["properties"].get("mag"),
          "type": f["properties"].get("type"), "place": f["properties"].get("place"), "alert": f["properties"].get("alert"),
          "lon": f["geometry"]["coordinates"][0], "lat": f["geometry"]["coordinates"][1], "url": f["properties"].get("url")} for f in j.get("features", [])]
    save("quakes.json", {"fetched": iso(NOW), "events": q})
    run["src"]["quakes"] = {"ok": True, "count": len(q), "newest": q[0]["t"] if q else None}
except Exception as e:
    run["src"]["quakes"] = {"ok": False, "err": repr(e)[:200]}

# 4 BIPAD 警报
try:
    rows = json.loads(get("https://bipadportal.gov.np/api/v1/alert/?format=json&ordering=-started_on&limit=30")).get("results", [])
    al = [{"title": r.get("title"), "started": r.get("startedOn"), "expire": r.get("expireOn"), "hazard": r.get("hazard"),
           "source": r.get("source"), "point": (r.get("point") or {}).get("coordinates")} for r in rows]
    save("alerts.json", {"fetched": iso(NOW), "alerts": al})
    run["src"]["alerts"] = {"ok": True, "newest": al[0]["started"] if al else None}
except Exception as e:
    run["src"]["alerts"] = {"ok": False, "err": repr(e)[:200]}

runs = load("runs.json", [])
runs.append(run)
cut = iso(NOW - dt.timedelta(days=3))
runs = [r for r in runs if r["t"] >= cut]
save("runs.json", runs)
print(json.dumps(run, ensure_ascii=False))
