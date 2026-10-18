"""事件证据包：把公开来源对齐到同一条时间线。在 GitHub 运行器上跑（events 分支的 evidence 工作流），只做小量取数和画图。

输入：Worker 自动发现的事件（https://everest-facets.yizebaba.workers.dev/api/events.json）
输出：events/<事件编号>.json（时间线）、events/<事件编号>_evn.png（IO.EVN 信号图）、index.json（目录）

每个证据包包含：
  - 事件本身的公开信号（BIPAD 警报、USGS、GDACS、水位越线）
  - IO.EVN 地震台（珠峰 Pyramid，GEOFON）和 KKN 地震台（Kakani，EarthScope）事件前 24 小时到后 3 小时的 1–5 Hz 信号包络，标出最强的几段，并核对两台是否一致
  - USGS、EMSC 在事件 300 km 内、前后一天的目录记录
  - 事件 80 km 内 BIPAD 水位站的当前状态（是否在报、是否越线）
  - 所在区的 IODA 网络连通（BGP、主动探测）前后变化
  - 哥白尼应急制图（Copernicus EMS）是否启动
  - Sentinel-1 / Sentinel-2 在事件前最近一景、事件后第一景（微软 Planetary Computer 目录，附预览链接）
  - 哥白尼全球洪水监测（GFM）自动洪水范围产品；IFRC Montandon 国际事件记录
  - 人工提交的证据（总览页“证据链 → 人工证据”，经 manual.json 进来）：已采信的列入时间线，待核实的只列指纹；链接会取一次内容算指纹并请求互联网档案馆存档
  - 每一版证据包都存一份不可变快照，并用 OpenTimestamps 加公开时间戳（之后升级为比特币区块确认）
只陈述公开来源记录了什么、什么时候；不判断成因，不预测。
"""
import json, math, os, re, sys, time, traceback
from datetime import datetime, timedelta, timezone
import urllib.request, urllib.parse, urllib.error

UA = {"user-agent": "everest-evidence (github.com/Yizebaba/EVEREST-)"}
EVN = (27.9587, 86.8117)
OUT = "events"
VERSION = 25   # 改了证据包内容时加 1，所有包会重算一次
NOW = datetime.now(timezone.utc)

# 尼泊尔区县 → IODA 地区（旧 14 区）
ZONE = {"Taplejung": "Mechi", "Sankhuwasabha": "Kosi", "Solukhumbu": "Sagarmatha", "Dolakha": "Janakpur", "Ramechhap": "Janakpur",
        "Sindhupalchok": "Bagmati", "Sindhupalchowk": "Bagmati", "Rasuwa": "Bagmati", "Nuwakot": "Bagmati", "Dhading": "Bagmati",
        "Gorkha": "Gandaki", "Lamjung": "Gandaki", "Manang": "Gandaki", "Kaski": "Gandaki", "Mustang": "Dhawalagiri", "Myagdi": "Dhawalagiri",
        "Dolpa": "Karnali", "Mugu": "Karnali", "Jumla": "Karnali", "Humla": "Karnali", "Kalikot": "Karnali", "Bajura": "Seti", "Bajhang": "Seti",
        "Darchula": "Mahakali"}
DIST = {"Taplejung": (27.62, 87.78), "Sankhuwasabha": (27.6, 87.3), "Solukhumbu": (27.79, 86.66), "Dolakha": (27.78, 86.17), "Ramechhap": (27.5, 86.08),
        "Sindhupalchok": (27.95, 85.69), "Rasuwa": (28.11, 85.3), "Nuwakot": (27.92, 85.17), "Dhading": (27.87, 84.92), "Gorkha": (28.3, 84.63),
        "Lamjung": (28.27, 84.36), "Manang": (28.67, 84.02), "Kaski": (28.32, 83.97), "Mustang": (28.98, 83.87), "Myagdi": (28.6, 83.5),
        "Dolpa": (29.0, 82.87), "Mugu": (29.55, 82.15), "Jumla": (29.27, 82.18), "Humla": (30.0, 81.8), "Kalikot": (29.15, 81.62),
        "Bajura": (29.5, 81.5), "Bajhang": (29.7, 81.2), "Darchula": (29.85, 80.75)}


RECEIPTS = []   # 本次生成证据包时的取数回执（见 receipt()）
SECRET_ENV = ("MONTANDON_API_TOKEN", "RELIEFWEB_APPNAME", "CF_RADAR_TOKEN", "FIRMS_MAP_KEY", "EARTHDATA_TOKEN", "GITHUB_TOKEN")


def redact(url):
    """回执里的网址去掉密钥：环境变量里的密钥值、以及 key/token/appname 一类参数的值。"""
    for k in SECRET_ENV:
        v = os.environ.get(k)
        if v and len(v) > 3: url = url.replace(v, "***")
    return re.sub(r"(?i)([?&](?:api_?key|key|token|access_token|appname|map_key)=)[^&]+", r"\1***", url)


def receipt(url, status, body, ctype, method):
    """取数回执：什么时间、向哪个网址、拿到了什么（SHA-256、字节数、类型）。
    小于 64 KB 的文本响应原样存一份（按哈希命名、gzip，同样内容只存一次），以后能拿出来对照；
    回执写进证据包，和证据包一起加时间戳、签名，证明“这个来源在那一刻返回过这些内容”。"""
    import hashlib, gzip
    h = hashlib.sha256(body).hexdigest()
    r = {"t": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "method": method, "url": redact(url), "status": status, "bytes": len(body), "sha256": h, "type": (ctype or "")[:60]}
    if len(body) <= 65536 and re.search(r"json|text|xml|csv|javascript", ctype or ""):
        d = os.path.join(OUT, "raw"); os.makedirs(d, exist_ok=True)
        f = os.path.join(d, h + ".gz")
        if not os.path.exists(f):
            with gzip.open(f, "wb") as g: g.write(body)
        r["body"] = "events/raw/" + h + ".gz"
    RECEIPTS.append(r)


def get(url, data=None, timeout=60, raw=False, headers=None):
    req = urllib.request.Request(url, data=data, headers={**UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        b = r.read()
        try: receipt(url, r.status, b, r.headers.get("content-type"), "POST" if data else "GET")
        except Exception: pass
    return b if raw else json.loads(b)


def iso(d):
    return d.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def P(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)


def km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    return 6371 * 2 * math.asin(math.sqrt(math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2))


# 10-18：一带一路样品（尼泊尔以外的项目所在国）。事件可以带 country（ISO3），默认尼泊尔；
# 尼泊尔专属的数据源（BIPAD 水位站、珠峰和加德满都两个地震台、尼泊尔分区）在别的国家不查。
CT = {"NPL": ("Nepal", "尼泊尔", "NP", "npl"), "PAK": ("Pakistan", "巴基斯坦", "PK", "pak"), "LAO": ("Laos", "老挝", "LA", "lao"), "CHN": ("China", "中国", "CN", "chn")}
def cty(ev): return CT.get(ev.get("country") or "NPL", CT["NPL"])


def nearest_district(lat, lon):
    return min(DIST, key=lambda d: km((lat, lon), DIST[d]))


def gaps_of(env, start, min_min=30):
    """找出没有数据的时段（合并缺口时填的 0 经滤波后会变成极小值，这里按背景的千分之一判断）。返回 [(开始, 结束)]。"""
    import numpy as np
    pos = env[env > 0]; bg = float(np.median(pos)) if len(pos) else 0
    bad = env <= bg * 1e-3 if bg > 0 else env <= 0
    out = []; i = 0
    while i < len(bad):
        if bad[i]:
            j = i
            while j < len(bad) and bad[j]: j += 1
            if j - i >= min_min: out.append((start + timedelta(minutes=i), start + timedelta(minutes=j)))
            i = j
        else:
            i += 1
    return out, bad


# ---------- 各证据 ----------
def evn(ev, t0, items, pack):
    """IO.EVN：1–5 Hz、60 秒均方根包络；背景取窗口中位数。"""
    a, b = t0 - timedelta(hours=24), t0 + timedelta(hours=3)
    dist = round(km((ev["lat"], ev["lon"]), EVN))
    if dist > 400: return   # 台站太远，记录不到这个事件
    try:
        from obspy import read
        import io
        raw = get(f"https://geofon.gfz.de/fdsnws/dataselect/1/query?net=IO&sta=EVN&cha=BHZ&starttime={iso(a)[:-1]}&endtime={iso(b)[:-1]}", raw=True, timeout=180)
        if not raw:
            raise RuntimeError("GEOFON 没有返回数据")
        st = read(io.BytesIO(raw)); st.merge(fill_value=0); tr = st[0]
        tr.detrend("demean"); tr.filter("bandpass", freqmin=1, freqmax=5, corners=4, zerophase=True)
        import numpy as np
        sr = tr.stats.sampling_rate; n = int(60 * sr); x = tr.data.astype(float)
        m = len(x) // n; env = np.sqrt((x[:m * n].reshape(m, n) ** 2).mean(axis=1))
        start = tr.stats.starttime.datetime.replace(tzinfo=timezone.utc)
        gp, bad = gaps_of(env, start); env = np.where(bad, 0.0, env)
        valid = env[env > 0]; bg = float(np.median(valid)) if len(valid) else 0
        cover = round(100 * len(valid) / max(1, int((b - a).total_seconds() / 60)))
        for g0, g1 in gp:
            items.append({"t": iso(g0), "src": "IO.EVN 地震台", "kind": "MISSING", "text": f"{iso(g0)[11:16]}–{iso(g1)[11:16]} UTC 没有数据（{int((g1 - g0).total_seconds() // 60)} 分钟）",
                          "text_en": f"No data {iso(g0)[11:16]}–{iso(g1)[11:16]} UTC ({int((g1 - g0).total_seconds() // 60)} min)"})
        peaks = []
        order = np.argsort(-env)
        for i in order:
            if bg <= 0 or env[i] / bg < 5 or len(peaks) >= 3:
                break
            ti = start + timedelta(minutes=int(i))
            if all(abs((ti - p[0]).total_seconds()) > 1800 for p in peaks):
                peaks.append((ti, float(env[i] / bg)))
        pack["evn"] = {"distance_km": dist, "coverage_pct": cover, "background": bg, "peaks": [[iso(p[0]), round(p[1], 1)] for p in peaks], "png": f"{ev['id']}_evn.png"}
        if peaks:
            for p in sorted(peaks):
                items.append({"t": iso(p[0]), "src": "IO.EVN 地震台", "kind": "SUPPORTING", "text_en": f"1–5 Hz signal about {p[1]:.0f}× background (station about {dist} km away; shows only that strong shaking was recorded, source not determined)", "text": f"1–5 Hz 信号约为背景的 {p[1]:.0f} 倍（台站距事件约 {dist} km；只说明此时有强信号，来源未判定）"})
        else:
            items.append({"t": iso(t0), "src": "IO.EVN 地震台", "kind": "NEUTRAL", "text_en": f"No signal above 5× background from 24 h before to 3 h after (about {dist} km away, {cover}% data coverage)", "text": f"事件前 24 小时到后 3 小时没有超过背景 5 倍的信号（距约 {dist} km，数据覆盖 {cover}%）"})
        if cover < 80:
            items.append({"t": iso(a), "src": "IO.EVN 地震台", "kind": "MISSING", "text_en": f"Data covers only {cover}% of the window", "text": f"窗口内数据只覆盖 {cover}%"})
        pack["_series_evn"] = (start, env / (bg or 1))
        pack["_evn_gaps"] = gp
    except Exception as e:
        pack["evn"] = {"distance_km": dist, "error": str(e)[:200]}
        items.append({"t": iso(t0), "src": "IO.EVN 地震台", "kind": "MISSING", "text_en": f"Waveform not available ({str(e)[:80]})", "text": f"取不到这段波形（{str(e)[:80]}）"})


KKN = (27.8008, 85.2788)   # 尼泊尔 Kakani 台（NK.KKN，EarthScope 公开）


def kkn(ev, t0, items, pack):
    """第二个台：NK.KKN（加德满都北面）。两个台同一时刻都有强信号，才更可能是区域性事件而不是 Pyramid 附近的冰崩。"""
    a, b = t0 - timedelta(hours=24), t0 + timedelta(hours=3)
    dist = round(km((ev["lat"], ev["lon"]), KKN))
    if dist > 400: return
    try:
        from obspy import read
        import io, numpy as np
        raw = get(f"https://service.iris.edu/fdsnws/dataselect/1/query?net=NK&sta=KKN&cha=BHZ&loc=*&starttime={iso(a)[:-1]}&endtime={iso(b)[:-1]}", raw=True, timeout=180)
        if not raw:
            raise RuntimeError("EarthScope 没有返回数据")
        st = read(io.BytesIO(raw)); st.merge(fill_value=0); tr = st[0]
        tr.detrend("demean"); tr.filter("bandpass", freqmin=1, freqmax=5, corners=4, zerophase=True)
        n = int(60 * tr.stats.sampling_rate); x = tr.data.astype(float); m = len(x) // n
        env = np.sqrt((x[:m * n].reshape(m, n) ** 2).mean(axis=1)); start = tr.stats.starttime.datetime.replace(tzinfo=timezone.utc)
        gp, bad = gaps_of(env, start); env = np.where(bad, 0.0, env)
        for g0, g1 in gp:
            items.append({"t": iso(g0), "src": "KKN 地震台", "kind": "MISSING", "text": f"{iso(g0)[11:16]}–{iso(g1)[11:16]} UTC 没有数据（{int((g1 - g0).total_seconds() // 60)} 分钟）",
                          "text_en": f"No data {iso(g0)[11:16]}–{iso(g1)[11:16]} UTC ({int((g1 - g0).total_seconds() // 60)} min)"})
        valid = env[env > 0]; bg = float(np.median(valid)) if len(valid) else 0
        cover = round(100 * len(valid) / max(1, int((b - a).total_seconds() / 60)))
        peaks = []
        for i in np.argsort(-env):
            if bg <= 0 or env[i] / bg < 5 or len(peaks) >= 3:
                break
            ti = start + timedelta(minutes=int(i))
            if all(abs((ti - p[0]).total_seconds()) > 1800 for p in peaks):
                peaks.append((ti, float(env[i] / bg)))
        pack["kkn"] = {"distance_km": dist, "coverage_pct": cover, "peaks": [[iso(p[0]), round(p[1], 1)] for p in peaks]}
        pack["_series_kkn"] = (start, env / (bg or 1))
        evp = [P(p[0]) for p in (pack.get("evn") or {}).get("peaks", [])]
        for p in sorted(peaks):
            both = any(abs((p[0] - q).total_seconds()) <= 180 for q in evp)
            evgap = any(g0 <= p[0] <= g1 for g0, g1 in (pack.get("_evn_gaps") or []))
            items.append({"t": iso(p[0]), "src": "KKN 地震台", "kind": "SUPPORTING",
                          "text": f"1–5 Hz 信号约为背景的 {p[1]:.0f} 倍（台站距事件约 {dist} km）" + ("；IO.EVN 同一时刻也有强信号，两台一致" if both else "；IO.EVN 这一时刻没有数据，无法核对" if evgap else "；IO.EVN 这一时刻没有强信号"),
                          "text_en": f"1–5 Hz signal about {p[1]:.0f}× background (station about {dist} km away)" + ("; IO.EVN also strong at the same time — both stations agree" if both else "; IO.EVN had no data then, cannot cross-check" if evgap else "; IO.EVN not strong at this time")})
        for q in evp:
            qi = int((q - start).total_seconds() // 60)
            has = 0 <= qi < len(env) and env[qi] > 0
            if not any(abs((q - p[0]).total_seconds()) <= 180 for p in peaks) and has:
                items.append({"t": iso(q), "src": "KKN 地震台", "kind": "CONTRADICTORY",
                              "text": "IO.EVN 这一时刻的强信号，KKN 没有记录到：更可能是珠峰附近的局部震动（如冰崩），不是这次事件",
                              "text_en": "KKN did not record IO.EVN's strong signal at this time: more likely local shaking near Everest (e.g. icefall), not this event"})
        if not peaks:
            items.append({"t": iso(t0), "src": "KKN 地震台", "kind": "NEUTRAL", "text": f"事件前 24 小时到后 3 小时没有超过背景 5 倍的信号（距约 {dist} km，覆盖 {cover}%）",
                          "text_en": f"No signal above 5× background from 24 h before to 3 h after (about {dist} km away, {cover}% coverage)"})
    except Exception as e:
        pack["kkn"] = {"distance_km": dist, "error": str(e)[:200]}
        items.append({"t": iso(t0), "src": "KKN 地震台", "kind": "MISSING", "text": f"取不到这段波形（{str(e)[:80]}）", "text_en": f"Waveform not available ({str(e)[:80]})"})


def catalogs(ev, t0, items):
    a, b = t0 - timedelta(days=1), t0 + timedelta(days=1)
    try:
        x = get(f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&latitude={ev['lat']}&longitude={ev['lon']}&maxradiuskm=300&starttime={iso(a)}&endtime={iso(b)}")
        for f in x.get("features", []):
            p = f["properties"]
            items.append({"t": iso(datetime.fromtimestamp(p["time"] / 1000, timezone.utc)), "src": "USGS 地震目录", "kind": "SUPPORTING",
                          "text_en": f"M{p['mag']} {'landslide/collapse (non-tectonic)' if p.get('type') == 'landslide' else p.get('type')} · {p.get('place')}", "text": f"M{p['mag']} {'崩塌/滑坡（非构造）' if p.get('type') == 'landslide' else p.get('type')} · {p.get('place')}", "url": p.get("url")})
        if not x.get("features"):
            items.append({"t": iso(t0), "src": "USGS 地震目录", "kind": "NEUTRAL", "text_en": "Nothing within 300 km in the day before or after", "text": "事件 300 km 内前后一天没有记录"})
    except Exception as e:
        items.append({"t": iso(t0), "src": "USGS 地震目录", "kind": "MISSING", "text_en": f"Query failed ({str(e)[:60]})", "text": f"查询失败（{str(e)[:60]}）"})
    try:
        rawb = get(f"https://www.seismicportal.eu/fdsnws/event/1/query?format=json&lat={ev['lat']}&lon={ev['lon']}&maxradius=2.7&start={iso(a)[:-1]}&end={iso(b)[:-1]}", raw=True)
        fs = json.loads(rawb).get("features", []) if rawb.strip() else []
        for f in fs:
            p = f["properties"]
            items.append({"t": p["time"][:19] + "Z", "src": "EMSC 地震目录", "kind": "SUPPORTING", "text_en": f"{p.get('magtype')} {p.get('mag')} · {p.get('flynn_region')}", "text": f"{p.get('magtype')} {p.get('mag')} · {p.get('flynn_region')}"})
        if not fs:
            items.append({"t": iso(t0), "src": "EMSC 地震目录", "kind": "NEUTRAL", "text_en": "Nothing within 300 km in the day before or after", "text": "事件 300 km 内前后一天没有记录"})
    except Exception as e:
        items.append({"t": iso(t0), "src": "EMSC 地震目录", "kind": "NEUTRAL", "text_en": ("Nothing within 300 km in the day before or after" if "204" in str(e) else f"Query failed ({str(e)[:60]})"), "text": "事件 300 km 内前后一天没有记录" if "204" in str(e) else f"查询失败（{str(e)[:60]}）"})


def gauges(ev, t0, items, pack):
    if cty(ev)[2] != "NP": return   # BIPAD 只有尼泊尔的站
    try:
        rows = []
        for off in range(0, 900, 100):
            r = get(f"https://bipadportal.gov.np/api/v1/river-stations/?format=json&limit=100&offset={off}").get("results", [])
            if not r:
                break
            rows += r
        near = []
        for r in rows:
            c = (r.get("point") or {}).get("coordinates")
            if not c:
                continue
            d = km((ev["lat"], ev["lon"]), (c[1], c[0]))
            if d <= 80:
                near.append((d, r))
        near.sort(key=lambda z: z[0])
        out = []
        for d, r in near[:12]:
            on = r.get("waterLevelOn"); rep = bool(on) and (NOW - P(on)).total_seconds() < 6 * 3600
            out.append({"id": r.get("stationSeriesId"), "title": r.get("title"), "km": round(d), "level": r.get("waterLevel"), "at": on,
                        "warning": r.get("warningLevel"), "danger": r.get("dangerLevel"), "status": r.get("status"), "reporting": rep})
        pack["gauges"] = out
        nrep = sum(1 for g in out if g["reporting"])
        items.append({"t": iso(NOW), "src": "BIPAD 水位站", "kind": "MISSING" if nrep < len(out) else "NEUTRAL",
                      "text_en": f"{len(out)} public gauges within 80 km, {nrep} reporting now" + ("; not reporting: " + ", ".join(g["title"] for g in out if not g["reporting"]) if nrep < len(out) else ""), "text": f"事件 80 km 内 {len(out)} 个公开水位站，现在在报 {nrep} 个" + ("；停报：" + "、".join(g["title"] for g in out if not g["reporting"]) if nrep < len(out) else "")})
    except Exception as e:
        items.append({"t": iso(NOW), "src": "BIPAD 水位站", "kind": "MISSING", "text_en": f"Query failed ({str(e)[:60]})", "text": f"查询失败（{str(e)[:60]}）"})


def ioda(ev, t0, items, pack):
    cc = cty(ev)[2]
    if cc == "NP":
        d = ev.get("district") or nearest_district(ev["lat"], ev["lon"]); z = ZONE.get(d)
    else:
        z = ev.get("ioda_region")
    if not z:
        return
    try:
        q = get(f"https://api.ioda.inetintel.cc.gatech.edu/v2/entities/query?entityType=region&search={urllib.parse.quote(z)}")
        ents = [e for e in q.get("data", []) if (e.get("attrs") or {}).get("country_code") == cc or cty(ev)[0] in json.dumps(e)]
        if not ents:
            raise RuntimeError("IODA 没有这个地区：" + z)
        code = ents[0]["code"]
        a, b = int((t0 - timedelta(hours=24)).timestamp()), int(min(NOW, t0 + timedelta(hours=24)).timestamp())
        x = get(f"https://api.ioda.inetintel.cc.gatech.edu/v2/signals/raw/region/{code}?from={a}&until={b}")
        flat = x["data"][0] if x.get("data") and isinstance(x["data"][0], list) else x.get("data", [])
        res = {"region": f"{z} ({code})"}
        for s in flat:
            if s.get("datasource") not in ("bgp", "ping-slash24"):
                continue
            v = [(s["from"] + i * s["step"], y) for i, y in enumerate(s.get("values") or []) if isinstance(y, (int, float))]
            if not v:
                continue
            before = [y for t, y in v if t < t0.timestamp()]; after = [y for t, y in v if t >= t0.timestamp()]
            base = sorted(before)[len(before) // 2] if before else None; low = min(after) if after else None
            res[s["datasource"]] = {"median_before": base, "min_after": low}
            if base and low is not None and low < 0.7 * base:
                tmin = min((t for t, y in v if t >= t0.timestamp() and y == low))
                items.append({"t": iso(datetime.fromtimestamp(tmin, timezone.utc)), "src": "IODA 网络连通", "kind": "SUPPORTING",
                              "text_en": f"{z} region {s['datasource']} fell from {base:.0f} to {low:.0f}", "text": f"{z} 区 {s['datasource']} 从 {base:.0f} 降到 {low:.0f}"})
        pack["ioda"] = res
        if not any(i["src"] == "IODA 网络连通" for i in items):
            items.append({"t": iso(t0), "src": "IODA 网络连通", "kind": "NEUTRAL", "text_en": f"No clear drop in {z} region within 24 h of the event", "text": f"{z} 区事件前后 24 小时没有明显下降"})
    except Exception as e:
        items.append({"t": iso(t0), "src": "IODA 网络连通", "kind": "MISSING", "text_en": f"Query failed ({str(e)[:60]})", "text": f"查询失败（{str(e)[:60]}）"})


def ems(ev, t0, items):
    """哥白尼应急制图（Copernicus EMS Rapid Mapping）和国际灾害宪章：是否为这次事件启动。"""
    try:
        x = get("https://rapidmapping.emergency.copernicus.eu/backend/dashboard-api/public-activations-info/?limit=60")
        hits = []
        for a in x.get("results", []):
            cs = " ".join(c.get("name", "") if isinstance(c, dict) else str(c) for c in (a.get("countries") or []))
            et = a.get("eventTime") or a.get("activationTime")
            if not any(w in cs for w in ([cty(ev)[0]] + (["China"] if cty(ev)[2] == "NP" else []))) or not et:
                continue
            t = P(et if ("Z" in et or "+" in et[10:]) else et + "Z")
            if t0 - timedelta(days=2) <= t <= t0 + timedelta(days=14):
                hits.append(a)
        for a in hits:
            ta = a.get("activationTime") or a.get("eventTime")
            items.append({"t": iso(P(ta if ("Z" in ta or "+" in ta[10:]) else ta + "Z")),
                          "src": "Copernicus EMS", "kind": "SUPPORTING",
                          "text_en": f"{a.get('code')} rapid mapping activated: {a.get('name')}" + (f"; International Charter {a.get('charterNumber')}" if a.get("charterNumber") else ""), "text": f"{a.get('code')} 启动应急制图：{a.get('name')}" + (f"；国际灾害宪章 {a.get('charterNumber')}" if a.get("charterNumber") else ""),
                          "url": f"https://rapidmapping.emergency.copernicus.eu/{a.get('code')}"})
        if not hits:
            items.append({"t": iso(NOW), "src": "Copernicus EMS", "kind": "NEUTRAL", "text_en": "No rapid mapping activated for this event", "text": "没有为这次事件启动应急制图"})
    except Exception as e:
        items.append({"t": iso(NOW), "src": "Copernicus EMS", "kind": "MISSING", "text_en": f"Query failed ({str(e)[:60]})", "text": f"查询失败（{str(e)[:60]}）"})


def sentinel(ev, t0, items, pack):
    bb = [ev["lon"] - 0.15, ev["lat"] - 0.15, ev["lon"] + 0.15, ev["lat"] + 0.15]
    res = {}
    for col, name in (("sentinel-1-rtc", "Sentinel-1 雷达"), ("sentinel-2-l2a", "Sentinel-2 光学")):
        def srch(dt, sort):
            body = {"collections": [col], "bbox": bb, "datetime": dt, "limit": 1, "sortby": [{"field": "properties.datetime", "direction": sort}]}
            if col == "sentinel-2-l2a":
                body["query"] = {"eo:cloud_cover": {"lt": 60}}
            r = get("https://planetarycomputer.microsoft.com/api/stac/v1/search", data=json.dumps(body).encode(), headers={"content-type": "application/json"})
            f = r.get("features", [])
            if not f:
                return None
            f = f[0]; pv = (f.get("assets", {}).get("rendered_preview") or {}).get("href")
            return {"id": f["id"], "t": f["properties"]["datetime"][:19] + "Z", "cloud": f["properties"].get("eo:cloud_cover"), "preview": pv,
                    "explore": f"https://planetarycomputer.microsoft.com/explore?c={ev['lon']:.3f},{ev['lat']:.3f}&z=11&d={col}"}
        try:
            before = srch(f"{iso(t0 - timedelta(days=40))}/{iso(t0)}", "desc")
            after = srch(f"{iso(t0)}/{iso(NOW)}", "asc")
            res[col] = {"before": before, "after": after}
            if before:
                items.append({"t": before["t"], "src": name, "kind": "NEUTRAL", "text_en": f"Last scene before the first public signal {before['id']}" + (f" (cloud {before['cloud']:.0f}%)" if before.get("cloud") is not None else ""), "text": f"第一条公开信号之前最近一景 {before['id']}" + (f"（云量 {before['cloud']:.0f}%）" if before.get("cloud") is not None else ""), "url": before.get("preview")})
            if after:
                items.append({"t": after["t"], "src": name, "kind": "SUPPORTING", "text_en": f"First scene after the first public signal {after['id']}" + (f" (cloud {after['cloud']:.0f}%)" if after.get("cloud") is not None else "") + ", compare with before", "text": f"第一条公开信号之后第一景 {after['id']}" + (f"（云量 {after['cloud']:.0f}%）" if after.get("cloud") is not None else "") + "，可与事件前对比", "url": after.get("preview")})
            else:
                items.append({"t": iso(NOW), "src": name, "kind": "MISSING", "text_en": "No new scene after the first public signal yet (filled in automatically)", "text": "第一条公开信号之后还没有新的一景（下次自动补）"})
        except Exception as e:
            items.append({"t": iso(NOW), "src": name, "kind": "MISSING", "text_en": f"Catalogue query failed ({str(e)[:60]})", "text": f"目录查询失败（{str(e)[:60]}）"})
    pack["sentinel"] = res


def gfm(ev, t0, items, pack):
    """哥白尼全球洪水监测（GFM）：事件前 2 天到后 7 天，事件 15 km 内每景 Sentinel-1 自动提取的洪水范围。"""
    bb = [ev["lon"] - 0.15, ev["lat"] - 0.15, ev["lon"] + 0.15, ev["lat"] + 0.15]
    try:
        body = {"collections": ["GFM"], "bbox": bb, "datetime": f"{iso(t0 - timedelta(days=2))}/{iso(min(NOW, t0 + timedelta(days=7)))}", "limit": 20}
        r = get("https://stac.eodc.eu/api/v1/search", data=json.dumps(body).encode(), headers={"content-type": "application/json"})
        fs = r.get("features", [])
        res = []
        for f in fs:
            a = f.get("assets", {})
            fl = next((k for k in a if "flood" in k.lower() and "extent" in k.lower()), None) or next((k for k in a if "flood" in k.lower()), None)
            res.append({"id": f["id"], "t": (f["properties"].get("datetime") or "")[:19] + "Z", "flood_asset": fl, "href": (a.get(fl) or {}).get("href") if fl else None})
        pack["gfm"] = {"scenes": res, "portal": f"https://portal.gfm.eodc.eu/?lat={ev['lat']}&lng={ev['lon']}&zoom=11"}
        for x in sorted(res, key=lambda z: z["t"]):
            items.append({"t": x["t"], "src": "哥白尼 GFM", "kind": "SUPPORTING" if P(x["t"]) >= t0 else "NEUTRAL",
                          "text": f"Sentinel-1 自动洪水范围产品 {x['id']}" + ("（含洪水范围图层）" if x["flood_asset"] else ""),
                          "text_en": f"Sentinel-1 automatic flood-extent product {x['id']}" + (" (flood-extent layer included)" if x["flood_asset"] else ""),
                          "url": x["href"] or pack["gfm"]["portal"]})
        if not res:
            items.append({"t": iso(NOW), "src": "哥白尼 GFM", "kind": "MISSING", "text": "事件前后没有覆盖这里的自动洪水范围产品（可能是山区阴影、雷达几何遮挡或还没过境）",
                          "text_en": "No automatic flood-extent product covering this place around the event (mountain shadow/layover, or no pass yet)"})
    except Exception as e:
        items.append({"t": iso(NOW), "src": "哥白尼 GFM", "kind": "MISSING", "text": f"查询失败（{str(e)[:60]}）", "text_en": f"Query failed ({str(e)[:60]})"})


def montandon(ev, t0, items, pack):
    """IFRC Montandon：国际通用的灾害事件记录（GDACS、GLIDE、EM-DAT、USGS 等统一编号）。"""
    url = "https://montandon-eoapi-stage.ifrc.org/stac/search"
    tok = os.environ.get("MONTANDON_API_TOKEN")
    body = {"collections": ["glide-events", "gdacs-events", "emdat-events", "usgs-events", "ifrcevent-events"],
            "bbox": [ev["lon"] - 1.0, ev["lat"] - 1.0, ev["lon"] + 1.0, ev["lat"] + 1.0],
            "datetime": f"{iso(t0 - timedelta(days=3))}/{iso(t0 + timedelta(days=3))}", "limit": 20}
    try:
        r = get(url, data=json.dumps(body).encode(), headers={"content-type": "application/json", **({"authorization": "Bearer " + tok} if tok else {})})
        fs = r.get("features", [])
        pack["montandon"] = [{"id": f["id"], "collection": f.get("collection"), "corr_id": f["properties"].get("monty:corr_id"), "title": f["properties"].get("title"), "t": f["properties"].get("datetime")} for f in fs]
        for f in pack["montandon"]:
            items.append({"t": (f["t"] or iso(t0))[:19] + "Z", "src": "IFRC Montandon", "kind": "SUPPORTING",
                          "text": f"国际事件记录 {f['collection']} · {f['title'] or f['id']}（关联编号 {f['corr_id']}）",
                          "text_en": f"International event record {f['collection']} · {f['title'] or f['id']} (correlation id {f['corr_id']})"})
        if not fs:
            items.append({"t": iso(NOW), "src": "IFRC Montandon", "kind": "NEUTRAL", "text": "国际灾害事件库里还没有这次事件", "text_en": "Not yet in the international disaster event registry"})
    except Exception as e:
        need = "401" in str(e) or "403" in str(e)
        items.append({"t": iso(NOW), "src": "IFRC Montandon", "kind": "MISSING",
                      "text": "需要 IFRC GO 账号令牌才能查询（未配置）" if need else f"查询失败（{str(e)[:60]}）",
                      "text_en": "Needs an IFRC GO account token (not configured)" if need else f"Query failed ({str(e)[:60]})"})


MANUAL = {"items": []}


def manual_sig(eid):
    return hashlib_sha([[i["mid"], i["status"], i.get("sha256")] for i in MANUAL["items"] if i.get("ev") == eid])


def hashlib_sha(o):
    import hashlib
    return hashlib.sha256(json.dumps(o, sort_keys=True).encode()).hexdigest()[:16]


def link_fingerprint(it):
    """链接类证据：取一次内容算 SHA-256（证明“那时那个网址返回的就是这些字节”），并请求互联网档案馆存一份。结果缓存在条目里。"""
    import hashlib
    if not it.get("url") or it.get("url_sha256"):
        return
    try:
        b = get(it["url"], raw=True, timeout=40)
        it["url_sha256"] = hashlib.sha256(b).hexdigest(); it["url_bytes"] = len(b); it["url_fetched"] = iso(NOW)
    except Exception as e:
        it["url_err"] = str(e)[:80]
    try:
        req = urllib.request.Request("https://web.archive.org/save/" + it["url"], headers=UA)
        with urllib.request.urlopen(req, timeout=60) as r:
            loc = r.headers.get("Content-Location") or r.geturl()
        if loc and "/web/" in loc:
            it["wayback"] = loc if loc.startswith("http") else "https://web.archive.org" + loc
    except Exception as e:
        it["wayback_err"] = str(e)[:80]


def manual(ev, t0, items, pack):
    """人工提交：已采信 → 列入时间线（标“人工提交，已核实”）；待核实 → 只列一条“有 N 条待核实，指纹已存证”。不采信的不列。"""
    mine = [i for i in MANUAL["items"] if i.get("ev") == ev["id"] and i["status"] != "rejected"]
    acc = [i for i in mine if i["status"] == "accepted"]
    pend = [i for i in mine if i["status"] == "pending"]
    KN = {"file": ("文件", "file"), "link": ("链接", "link"), "note": ("现场记录", "field note")}
    for i in acc:
        link_fingerprint(i)
        k = KN.get(i.get("kind"), (i.get("kind") or "", i.get("kind") or ""))
        fp = i.get("sha256") or i.get("url_sha256")
        extra = (f"；指纹 {fp[:12]}…" if fp else "") + ("；已存互联网档案馆" if i.get("wayback") else "")
        extra_en = (f"; fingerprint {fp[:12]}…" if fp else "") + ("; archived on the Wayback Machine" if i.get("wayback") else "")
        c2 = i.get("c2pa") or {}
        if c2.get("has"): extra += f"；带 C2PA 来源记录（{c2.get('gen') or '生成工具未知'}）"; extra_en += f"; carries C2PA provenance ({c2.get('gen') or 'generator unknown'})"
        if i.get("exif_time"): extra += f"；相机记录的拍摄时间 {i['exif_time']}"; extra_en += f"; camera time {i['exif_time']}"
        items.append({"t": i.get("when") or i.get("submitted"), "src": "人工提交", "kind": "SUPPORTING", "mid": i["mid"],
                      "text": f"{k[0]}：{i.get('title', '')}" + (f"（{i['place']}）" if i.get("place") else "") + (f"，来源 {i['src']}" if i.get("src") else "") + f"。已核实{extra}",
                      "text_en": f"{k[1]}: {i.get('title', '')}" + (f" ({i['place']})" if i.get("place") else "") + (f", source {i['src']}" if i.get("src") else "") + f". Verified{extra_en}",
                      "url": i.get("wayback") or i.get("url")})
    if pend:
        items.append({"t": max(i.get("submitted") or iso(t0) for i in pend), "src": "人工提交", "kind": "NEUTRAL",
                      "text": f"有 {len(pend)} 条人工提交的证据待核实，只公开指纹：" + "、".join((i.get("sha256") or i["mid"])[:12] for i in pend),
                      "text_en": f"{len(pend)} submitted item(s) awaiting verification; only fingerprints are public: " + ", ".join((i.get("sha256") or i["mid"])[:12] for i in pend)})
    pack["manual"] = {"accepted": len(acc), "pending": len(pend)}


def ots_stamp(eid, path, idx_entry):
    """OpenTimestamps：给这一版证据包加公开时间戳。存一份不再改动的快照 events/archive/<编号>_<哈希前12位>.json 和对应 .ots。"""
    import hashlib, shutil, subprocess
    b = open(path, "rb").read(); h = hashlib.sha256(b).hexdigest()
    os.makedirs(os.path.join(OUT, "archive"), exist_ok=True)
    snap = os.path.join(OUT, "archive", f"{eid}_{h[:12]}.json")
    stamps = idx_entry.setdefault("ots", [])
    if any(x["sha256"] == h for x in stamps):
        return
    shutil.copyfile(path, snap)
    r = subprocess.run(["ots", "stamp", snap], capture_output=True, text=True, timeout=120)
    ok = os.path.exists(snap + ".ots")
    stamps.append({"sha256": h, "file": f"events/archive/{os.path.basename(snap)}", "ots": f"events/archive/{os.path.basename(snap)}.ots",
                   "stamped": iso(NOW), "status": "pending" if ok else "failed", "err": None if ok else (r.stderr or r.stdout)[-200:],
                   "tsa": tsa_stamp(snap), "sigstore": sigstore_sign(snap)})


SIG_ID = "https://github.com/Yizebaba/EVEREST-/.github/workflows/evidence.yml@refs/heads/events"


def sigstore_sign(path):
    """Sigstore 无密钥签名（GitHub Actions 的身份令牌）：证明这份快照是本仓库 evidence.yml 生成的，签名同时记入公开透明日志 Rekor。
    存 <快照>.sigstore.json。核对：cosign verify-blob --bundle 快照.sigstore.json --certificate-identity <SIG_ID>
      --certificate-oidc-issuer https://token.actions.githubusercontent.com 快照"""
    import shutil, subprocess
    if not shutil.which("cosign") or not os.environ.get("ACTIONS_ID_TOKEN_REQUEST_URL"):
        return None
    b = path + ".sigstore.json"
    # 标准 Sigstore bundle 格式（cosign、sigstore-python 等工具都能核对）；旧版 cosign 不支持时退回旧格式
    r = subprocess.run(["cosign", "sign-blob", "--yes", "--new-bundle-format", "--bundle", b, path], capture_output=True, text=True, timeout=120)
    if not os.path.exists(b):
        r = subprocess.run(["cosign", "sign-blob", "--yes", "--bundle", b, path], capture_output=True, text=True, timeout=120)
    if not os.path.exists(b):
        return {"err": (r.stderr or r.stdout)[-160:]}
    v = subprocess.run(["cosign", "verify-blob", path, "--bundle", b, "--certificate-identity", SIG_ID,
                        "--certificate-oidc-issuer", "https://token.actions.githubusercontent.com"], capture_output=True, text=True, timeout=120)
    idx = None
    try:
        j = json.load(open(b))
        idx = ((j.get("verificationMaterial") or {}).get("tlogEntries") or [{}])[0].get("logIndex") or ((j.get("rekorBundle") or {}).get("Payload") or {}).get("logIndex")
    except Exception:
        pass
    return {"file": "events/archive/" + os.path.basename(b), "identity": SIG_ID, "rekor_log_index": idx, "self_verified": v.returncode == 0,
            "rekor": f"https://search.sigstore.dev/?logIndex={idx}" if idx else None}


TSA = {"FreeTSA": "https://freetsa.org/tsr", "DigiCert": "http://timestamp.digicert.com"}


def tsa_stamp(path):
    """RFC 3161 可信时间戳（两家时间戳机构，几秒内返回；和比特币时间戳互为备份）。存 <快照>.<机构>.tsr，返回机构签出的时间。
    核对：openssl ts -verify -in 快照.FreeTSA.tsr -data 快照 -CAfile freetsa_cacert.pem -untrusted freetsa_tsa.crt"""
    import subprocess
    out = []
    q = path + ".tsq"
    subprocess.run(["openssl", "ts", "-query", "-data", path, "-sha256", "-cert", "-no_nonce", "-out", q], capture_output=True, timeout=30)
    if not os.path.exists(q): return out
    for name, url in TSA.items():
        try:
            rep = get(url, data=open(q, "rb").read(), raw=True, timeout=30, headers={"content-type": "application/timestamp-query"})
            f = f"{path}.{name}.tsr"; open(f, "wb").write(rep)
            txt = subprocess.run(["openssl", "ts", "-reply", "-in", f, "-text"], capture_output=True, text=True, timeout=30).stdout
            m = re.search(r"Time stamp: (.+)", txt)
            out.append({"tsa": name, "file": "events/archive/" + os.path.basename(f), "time": m.group(1).strip() if m else None})
        except Exception as e:
            out.append({"tsa": name, "err": str(e)[:80]})
    os.remove(q)
    return out


def prov_export(pack):
    """W3C PROV-JSON：每条证据是一个实体，归属到发布它的来源（代理），带生成时间；证据包由这些实体派生。"""
    eid = pack["id"]; doc = {"prefix": {"ev": "https://github.com/Yizebaba/EVEREST-/blob/events/events/", "src": "https://github.com/Yizebaba/EVEREST-/source/", "everest": "https://github.com/Yizebaba/EVEREST-#"},
                            "entity": {}, "agent": {}, "activity": {}, "wasAttributedTo": {}, "wasDerivedFrom": {}, "wasGeneratedBy": {}}
    act = f"ev:{eid}#build-{pack['built']}"
    doc["activity"][act] = {"prov:startTime": pack["built"], "prov:type": "EVEREST evidence pack build", "prov:label": f"evidence_pack.py v{VERSION}"}
    doc["entity"][f"ev:{eid}.json"] = {"prov:type": "EvidencePack", "prov:label": pack.get("title"), "everest:hips": " ".join(pack.get("hips") or [])}
    doc["wasGeneratedBy"]["_:g0"] = {"prov:entity": f"ev:{eid}.json", "prov:activity": act, "prov:time": pack["built"]}
    for k, it in enumerate(pack.get("timeline", [])):
        import hashlib
        e = f"ev:{eid}.json_item{k}"; a = "src:s" + hashlib.sha1(it["src"].encode()).hexdigest()[:10]
        doc["entity"][e] = {"everest:kind": it["kind"], "prov:label": it.get("text_en") or it["text"], "prov:generatedAtTime": it["t"], **({"prov:location": it["url"]} if it.get("url") else {}),
                              **({"everest:cannotShow": (pack.get("bounds") or {}).get(it["bound"], {}).get("cannot")} if it.get("bound") else {})}
        doc["agent"].setdefault(a, {"prov:type": "prov:Organization", "prov:label": it["src"]})
        doc["wasAttributedTo"][f"_:a{k}"] = {"prov:entity": e, "prov:agent": a}
        doc["wasDerivedFrom"][f"_:d{k}"] = {"prov:generatedEntity": f"ev:{eid}.json", "prov:usedEntity": e}
    json.dump(doc, open(os.path.join(OUT, eid + ".prov.json"), "w"), ensure_ascii=False, indent=1)


def rocrate_export(pack, idx_entry):
    """RO-Crate 1.1 描述：把证据包、信号图、PROV、存证快照和时间戳文件打成一个标准研究对象（以后可整包存 Zenodo 拿 DOI）。"""
    eid = pack["id"]; base = "https://raw.githubusercontent.com/Yizebaba/EVEREST-/events/"
    parts = [{"@id": base + f"events/{eid}.json", "@type": "File", "name": "证据包（时间线）", "encodingFormat": "application/json"},
             {"@id": base + f"events/{eid}.prov.json", "@type": "File", "name": "W3C PROV 溯源记录", "encodingFormat": "application/json", "conformsTo": {"@id": "https://www.w3.org/TR/prov-json/"}}]
    if pack.get("png"): parts.append({"@id": base + f"events/{pack['png']}", "@type": "File", "name": "地震台信号图", "encodingFormat": "image/png"})
    for st in (idx_entry.get("ots") or [])[-3:]:
        parts.append({"@id": base + st["file"], "@type": "File", "name": "不可变快照", "sha256": st["sha256"], "dateCreated": st["stamped"]})
        parts.append({"@id": base + st["ots"], "@type": "File", "name": "OpenTimestamps 证明", "encodingFormat": "application/vnd.opentimestamps"})
        for t in st.get("tsa") or []:
            if t.get("file"): parts.append({"@id": base + t["file"], "@type": "File", "name": f"RFC 3161 时间戳（{t['tsa']}）", "encodingFormat": "application/timestamp-reply"})
        if (st.get("sigstore") or {}).get("file"):
            parts.append({"@id": base + st["sigstore"]["file"], "@type": "File", "name": "Sigstore 签名（含 Rekor 透明日志记录）", "encodingFormat": "application/vnd.dev.sigstore.bundle+json"})
    crate = {"@context": "https://w3id.org/ro/crate/1.1/context", "@graph": [
        {"@id": "ro-crate-metadata.json", "@type": "CreativeWork", "conformsTo": {"@id": "https://w3id.org/ro/crate/1.1"}, "about": {"@id": "./"}},
        {"@id": "./", "@type": "Dataset", "name": f"EVEREST 事件证据包：{pack.get('title')}", "description": pack.get("note"), "datePublished": pack["built"],
         "license": {"@id": "https://creativecommons.org/licenses/by/4.0/"}, "keywords": pack.get("hips") or [], "spatialCoverage": {"@id": "#place"},
         "temporalCoverage": pack["t"], "publisher": {"@id": "https://github.com/Yizebaba/EVEREST-"}, "hasPart": [{"@id": p["@id"]} for p in parts],
         "citation": [{"@id": d} for d in dict.fromkeys(x["doi"] for r in pack.get("references", []) for x in r["data_papers"] if x.get("doi"))]},
        *{x["doi"]: {"@id": x["doi"], "@type": "ScholarlyArticle", "name": x.get("title"), "datePublished": str(x.get("year") or "")}
          for r in pack.get("references", []) for x in r["data_papers"] if x.get("doi")}.values(),
        {"@id": "#place", "@type": "Place", "name": pack.get("place") or "", "geo": {"@id": "#geo"}},
        {"@id": "#geo", "@type": "GeoCoordinates", "latitude": pack["lat"], "longitude": pack["lon"]},
        {"@id": "https://github.com/Yizebaba/EVEREST-", "@type": "Organization", "name": "EVEREST"}] + parts}
    os.makedirs(os.path.join(OUT, "crates", eid), exist_ok=True)
    json.dump(crate, open(os.path.join(OUT, "crates", eid, "ro-crate-metadata.json"), "w"), ensure_ascii=False, indent=1)


def ots_upgrade(idx):
    """把还在等待的时间戳升级为比特币区块确认（通常几小时后可升级）。"""
    import subprocess
    for e in list(idx["events"].values()) + [idx.get("manual") or {}]:
        for x in e.get("ots", []):
            if x.get("status") != "pending" or not os.path.exists(x["ots"]):
                continue
            subprocess.run(["ots", "upgrade", x["ots"]], capture_output=True, text=True, timeout=120)
            info = subprocess.run(["ots", "info", x["ots"]], capture_output=True, text=True, timeout=60).stdout
            m = re.search(r"BitcoinBlockHeaderAttestation\((\d+)\)", info)
            if m:
                x["status"] = "confirmed"; x["bitcoin_block"] = int(m.group(1)); x["confirmed_checked"] = iso(NOW)


def plot_seis(ev, t0, pack):
    """两台站的 1–5 Hz 包络（相对各自背景，对数刻度），上下对齐；没有数据的分钟留空，不画成 0。"""
    S = [(k, pack.get(k)) for k in ("_series_evn", "_series_kkn") if pack.get(k)]
    if not S:
        return
    import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, axs = plt.subplots(len(S), 1, figsize=(9, 1.7 * len(S) + 0.5), dpi=90, sharex=True, squeeze=False)
    names = {"_series_evn": f"IO.EVN (Everest, {(pack.get('evn') or {}).get('distance_km', '?')} km)", "_series_kkn": f"NK.KKN (Kakani, {(pack.get('kkn') or {}).get('distance_km', '?')} km)"}
    for ax, (k, (start, y)) in zip(axs[:, 0], S):
        y = np.where(y > 0, y, np.nan); ts = [start + timedelta(minutes=i) for i in range(len(y))]
        ax.plot(ts, y, lw=0.7, color="#d9822b"); ax.set_yscale("log"); ax.axhline(1, color="#999", lw=0.5); ax.axhline(5, color="#c33", lw=0.4, ls=":")
        ax.axvline(t0, color="#3b82f6", lw=1, ls="--"); ax.set_ylabel("x bg", fontsize=7); ax.set_title(names[k], fontsize=8, loc="left"); ax.tick_params(labelsize=7)
    fig.suptitle(f"1-5 Hz, 60 s RMS  |  {ev['id']}  |  blue dashed = first public signal, red dotted = 5x background", fontsize=8)
    fig.autofmt_xdate(); fig.tight_layout(); fig.savefig(os.path.join(OUT, f"{ev['id']}_evn.png")); plt.close(fig)
    pack["png"] = f"{ev['id']}_evn.png"


# ---------- v9：更多公开记录（见 docs/EVIDENCE_SOURCES.md） ----------
def _env(raw, a, b):
    """MiniSEED → 1–5 Hz、60 秒均方根包络、缺口。返回 (起点, 包络, 缺口, 背景, 覆盖率)。"""
    from obspy import read
    import io, numpy as np
    st = read(io.BytesIO(raw)); st.merge(fill_value=0); tr = st[0]
    tr.detrend("demean"); tr.filter("bandpass", freqmin=1, freqmax=5, corners=4, zerophase=True)
    n = int(60 * tr.stats.sampling_rate); x = tr.data.astype(float); m = len(x) // n
    env = np.sqrt((x[:m * n].reshape(m, n) ** 2).mean(axis=1)); start = tr.stats.starttime.datetime.replace(tzinfo=timezone.utc)
    gp, bad = gaps_of(env, start); env = np.where(bad, 0.0, env)
    valid = env[env > 0]; bg = float(np.median(valid)) if len(valid) else 0
    return start, env, gp, bg, round(100 * len(valid) / max(1, int((b - a).total_seconds() / 60)))


def rshake(ev, t0, items, pack):
    """Raspberry Shake 民间地震仪（AM 台网）：事件 150 km 内最近的两台，事件前 6 小时到后 3 小时的强信号。"""
    base = "https://data.raspberryshake.org/fdsnws"
    a, b = t0 - timedelta(hours=6), t0 + timedelta(hours=3)
    try:
        txt = get(f"{base}/station/1/query?network=AM&latitude={ev['lat']}&longitude={ev['lon']}&maxradius=1.35&level=channel&format=text&starttime={iso(a)[:-1]}&endtime={iso(b)[:-1]}", raw=True, timeout=60).decode()
        st = {}
        for ln in txt.splitlines()[1:]:
            c = ln.split("|")
            if len(c) > 5 and c[3] in ("EHZ", "SHZ", "HHZ"):
                st.setdefault(c[1], (float(c[4]), float(c[5]), c[3], c[2]))
        near = sorted(((km((ev["lat"], ev["lon"]), (v[0], v[1])), k, v) for k, v in st.items()))[:2]
        pack["rshake"] = {"stations": [{"sta": k, "km": round(d)} for d, k, v in near]}
        if not near:
            items.append({"t": iso(t0), "src": "Raspberry Shake 地震仪", "kind": "MISSING", "text": "事件 150 km 内这段时间没有在线的民间地震仪",
                          "text_en": "No citizen seismometer online within 150 km during this window"})
            return
        for d, k, v in near:
            try:
                raw = get(f"{base}/dataselect/1/query?network=AM&station={k}&location={v[3] or '00'}&channel={v[2]}&starttime={iso(a)[:-1]}&endtime={iso(b)[:-1]}", raw=True, timeout=180)
                if not raw:
                    raise RuntimeError("没有返回数据")
                start, env, gp, bg, cover = _env(raw, a, b)
                import numpy as np
                pk = []
                for i in np.argsort(-env):
                    if bg <= 0 or env[i] / bg < 5 or len(pk) >= 2: break
                    ti = start + timedelta(minutes=int(i))
                    if all(abs((ti - q[0]).total_seconds()) > 1800 for q in pk): pk.append((ti, float(env[i] / bg)))
                for ti, r in pk:
                    items.append({"t": iso(ti), "src": "Raspberry Shake 地震仪", "kind": "SUPPORTING",
                                  "text": f"AM.{k}（距事件约 {d:.0f} km）1–5 Hz 信号约为背景的 {r:.0f} 倍", "text_en": f"AM.{k} (about {d:.0f} km away) 1–5 Hz signal about {r:.0f}× background"})
                if not pk:
                    items.append({"t": iso(t0), "src": "Raspberry Shake 地震仪", "kind": "NEUTRAL",
                                  "text": f"AM.{k}（距约 {d:.0f} km，覆盖 {cover}%）事件前 6 小时到后 3 小时没有超过背景 5 倍的信号",
                                  "text_en": f"AM.{k} (about {d:.0f} km, {cover}% coverage): nothing above 5× background from 6 h before to 3 h after"})
            except Exception as e:
                items.append({"t": iso(t0), "src": "Raspberry Shake 地震仪", "kind": "MISSING", "text": f"AM.{k} 取不到波形（{str(e)[:60]}）", "text_en": f"AM.{k} waveform not available ({str(e)[:60]})"})
    except Exception as e:
        items.append({"t": iso(t0), "src": "Raspberry Shake 地震仪", "kind": "MISSING", "text": f"台站查询失败（{str(e)[:60]}）", "text_en": f"Station query failed ({str(e)[:60]})"})


def usgs_products(ev, t0, items, pack):
    """USGS 每次地震的附加产品：ShakeMap 烈度、Did You Feel It? 有感报告、PAGER 模型估计（标明是估计，不是观测）。"""
    a, b = t0 - timedelta(days=1), t0 + timedelta(days=1)
    try:
        x = get(f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&latitude={ev['lat']}&longitude={ev['lon']}&maxradiuskm=300&starttime={iso(a)}&endtime={iso(b)}&minmagnitude=4")
        for f in x.get("features", [])[:5]:
            d = get(f["properties"]["detail"]); pr = d["properties"].get("products", {}); t = iso(datetime.fromtimestamp(d["properties"]["time"] / 1000, timezone.utc))
            sm = (pr.get("shakemap") or [{}])[0].get("properties", {}); dy = (pr.get("dyfi") or [{}])[0].get("properties", {}); pg = (pr.get("losspager") or [{}])[0].get("properties", {})
            if sm.get("maxmmi"):
                items.append({"t": t, "src": "USGS ShakeMap", "kind": "SUPPORTING", "text": f"M{f['properties']['mag']} 最大烈度 {float(sm['maxmmi']):.1f}（台站实测与模型合成的震动图）",
                              "text_en": f"M{f['properties']['mag']} max intensity {float(sm['maxmmi']):.1f} (shaking map from station records and model)", "url": f["properties"]["url"] + "/shakemap"})
            if dy.get("num-responses"):
                items.append({"t": t, "src": "USGS 有感报告", "kind": "SUPPORTING", "text": f"{dy['num-responses']} 份公众有感报告，最大烈度 {dy.get('maxmmi')}",
                              "text_en": f"{dy['num-responses']} public felt reports, max intensity {dy.get('maxmmi')}", "url": f["properties"]["url"] + "/dyfi"})
            if pg.get("alertlevel"):
                items.append({"t": t, "src": "USGS PAGER", "kind": "NEUTRAL", "text": f"机构模型估计：PAGER 警报级别 {pg['alertlevel']}（模型估计，不是观测）",
                              "text_en": f"Agency model estimate: PAGER alert level {pg['alertlevel']} (model estimate, not an observation)", "url": f["properties"]["url"] + "/pager"})
    except Exception as e:
        items.append({"t": iso(t0), "src": "USGS ShakeMap", "kind": "MISSING", "text": f"查询失败（{str(e)[:60]}）", "text_en": f"Query failed ({str(e)[:60]})"})


HAZ_EN = "(flood OR landslide OR avalanche OR earthquake OR \"glacial lake\" OR \"debris flow\" OR snowstorm OR rockfall)"


def place_word(ev):
    if cty(ev)[2] != "NP": return ev.get("place_word") or cty(ev)[0]
    d = ev.get("district") or (nearest_district(ev["lat"], ev["lon"]) if km((ev["lat"], ev["lon"]), DIST[nearest_district(ev["lat"], ev["lon"])]) < 60 else None)
    return d or "Nepal"


def gdelt(ev, t0, items, pack):
    """GDELT 全球新闻：这个地方的灾害新闻最早什么时候出现、有多少家媒体报道。"""
    a, b = t0 - timedelta(days=1), min(NOW, t0 + timedelta(days=5))
    q = f'"{place_word(ev)}" {HAZ_EN}' + ("" if place_word(ev) == cty(ev)[0] else " " + cty(ev)[0]) + " sourcelang:english"
    try:
        u = "https://api.gdeltproject.org/api/v2/doc/doc?" + urllib.parse.urlencode({"query": q, "mode": "artlist", "maxrecords": 75, "format": "json", "sort": "dateasc",
                                                                                     "startdatetime": a.strftime("%Y%m%d%H%M%S"), "enddatetime": b.strftime("%Y%m%d%H%M%S")})
        raw = b""
        for wait in (8, 30):   # GDELT 要求每 5 秒最多一次；共用的 GitHub 运行器常被限流，只退避一次，取不到就标缺失（附近新闻已由灾种扫描的 RSS 挂进来）
            time.sleep(wait)
            try:
                raw = get(u, raw=True, timeout=60); break
            except Exception as e:
                if "429" not in str(e) or wait == 30: raise
        if not raw.strip().startswith(b"{"):
            print("GDELT 返回：", q, raw[:300])
            if raw.strip(): raise RuntimeError("GDELT：" + raw[:80].decode(errors="ignore"))
        arts = json.loads(raw).get("articles", []) if raw.strip().startswith(b"{") else []
        HZ = re.compile(r"flood|landslide|avalanche|earthquake|quake|glacial|debris|snow|rockfall|inundat|deluge|swept|disaster|rescue|missing|dead|killed", re.I)
        arts = [x for x in arts if HZ.search(x.get("title", ""))]   # 标题里要有灾害相关的词，排除新闻汇总页
        news = [{"t": datetime.strptime(x["seendate"], "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "title": x.get("title", "")[:160], "url": x.get("url"), "domain": x.get("domain"), "lang": x.get("language")} for x in arts]
        pack["news"] = news[:20]
        if news:
            f0 = news[0]; doms = sorted({n["domain"] for n in news})
            items.append({"t": f0["t"], "src": "GDELT 新闻", "kind": "SUPPORTING", "text": f"最早一篇相关报道（{f0['domain']}）：{f0['title']}", "text_en": f"Earliest related report ({f0['domain']}): {f0['title']}", "url": f0["url"]})
            items.append({"t": news[-1]["t"], "src": "GDELT 新闻", "kind": "NEUTRAL", "text": f"事件前 1 天到后 5 天共 {len(news)} 篇、{len(doms)} 家媒体：{'、'.join(doms[:6])}", "text_en": f"{len(news)} articles from {len(doms)} outlets between 1 day before and 5 days after: {', '.join(doms[:6])}"})
        else:
            items.append({"t": iso(t0), "src": "GDELT 新闻", "kind": "NEUTRAL", "text": f"没有找到“{place_word(ev)}”的相关新闻", "text_en": f"No related news found for “{place_word(ev)}”"})
    except Exception as e:
        items.append({"t": iso(t0), "src": "GDELT 新闻", "kind": "MISSING", "text": f"查询失败（{str(e)[:60]}）", "text_en": f"Query failed ({str(e)[:60]})"})


def wiki(ev, t0, items, pack):
    """维基百科：事件后新建的相关条目（创建时间是公开、不可改的记录）。"""
    try:
        q = f"{place_word(ev)} {t0.year} " + ("flood" if "洪" in (ev.get("kind") or "") else "disaster")
        x = get("https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode({"action": "query", "list": "search", "srsearch": q, "format": "json", "srlimit": 5}))
        hits = 0
        for r in x.get("query", {}).get("search", []):
            y = get("https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode({"action": "query", "prop": "revisions", "titles": r["title"], "rvlimit": 1, "rvdir": "newer", "rvprop": "timestamp", "format": "json"}))
            pg = next(iter(y["query"]["pages"].values())); ts = (pg.get("revisions") or [{}])[0].get("timestamp")
            if ts and P(ts) >= t0 - timedelta(days=1):
                hits += 1
                items.append({"t": ts, "src": "维基百科", "kind": "SUPPORTING", "text": f"新建条目：{r['title']}", "text_en": f"Article created: {r['title']}", "url": "https://en.wikipedia.org/wiki/" + urllib.parse.quote(r["title"].replace(" ", "_"))})
        if not hits:
            items.append({"t": iso(t0), "src": "维基百科", "kind": "NEUTRAL", "text": "事件后没有新建的相关条目", "text_en": "No related article created after the event"})
    except Exception as e:
        items.append({"t": iso(t0), "src": "维基百科", "kind": "MISSING", "text": f"查询失败（{str(e)[:60]}）", "text_en": f"Query failed ({str(e)[:60]})"})


def hdx(ev, t0, items, pack):
    """OCHA HDX：事件后新建的尼泊尔人道数据集。"""
    try:
        fq = f"groups:{cty(ev)[3]} AND metadata_created:[{iso(t0 - timedelta(days=1))} TO NOW]"
        x = get("https://data.humdata.org/api/3/action/package_search?" + urllib.parse.urlencode({"q": "flood OR landslide OR avalanche OR earthquake OR disaster", "fq": fq, "sort": "metadata_created asc", "rows": 10}))
        rs = (x.get("result") or {}).get("results", [])
        for r in rs[:5]:
            items.append({"t": r["metadata_created"][:19] + "Z", "src": "OCHA HDX", "kind": "SUPPORTING", "text": f"新数据集：{r.get('title')}（{(r.get('organization') or {}).get('title', '')}）",
                          "text_en": f"New dataset: {r.get('title')} ({(r.get('organization') or {}).get('title', '')})", "url": "https://data.humdata.org/dataset/" + r["name"]})
        if not rs:
            items.append({"t": iso(t0), "src": "OCHA HDX", "kind": "NEUTRAL", "text": f"事件后没有新建的{cty(ev)[1]}灾害数据集", "text_en": f"No new {cty(ev)[0]} disaster dataset after the event"})
    except Exception as e:
        items.append({"t": iso(t0), "src": "OCHA HDX", "kind": "MISSING", "text": f"查询失败（{str(e)[:60]}）", "text_en": f"Query failed ({str(e)[:60]})"})


def reliefweb(ev, t0, items, pack):
    """ReliefWeb 人道报告（需要申请 appname，放在机密 RELIEFWEB_APPNAME）。"""
    app = os.environ.get("RELIEFWEB_APPNAME")
    if not app:
        items.append({"t": iso(NOW), "src": "ReliefWeb", "kind": "MISSING", "text": "需要申请 ReliefWeb appname（未配置）", "text_en": "Needs a ReliefWeb appname (not configured)"}); return
    try:
        body = {"query": {"value": f"{cty(ev)[0]} {place_word(ev)}"}, "filter": {"field": "date.created", "value": {"from": iso(t0 - timedelta(days=1))}}, "sort": ["date.created:asc"], "limit": 10, "fields": {"include": ["title", "url", "date.created", "source.shortname"]}}
        x = get(f"https://api.reliefweb.int/v2/reports?appname={urllib.parse.quote(app)}", data=json.dumps(body).encode(), headers={"content-type": "application/json"})
        for r in x.get("data", [])[:6]:
            f = r["fields"]; items.append({"t": f["date"]["created"][:19] + "Z", "src": "ReliefWeb", "kind": "SUPPORTING", "text": f"{', '.join(s['shortname'] for s in f.get('source', []))}：{f['title']}", "text_en": f"{', '.join(s['shortname'] for s in f.get('source', []))}: {f['title']}", "url": f.get("url")})
        if not x.get("data"):
            items.append({"t": iso(t0), "src": "ReliefWeb", "kind": "NEUTRAL", "text": "事件后没有相关人道报告", "text_en": "No related humanitarian report after the event"})
    except Exception as e:
        items.append({"t": iso(t0), "src": "ReliefWeb", "kind": "MISSING", "text": f"查询失败（{str(e)[:60]}）", "text_en": f"Query failed ({str(e)[:60]})"})


def cfradar(ev, t0, items, pack):
    """Cloudflare Radar：尼泊尔的网络中断和流量异常记录（和 IODA 互相核对）。需要 API 令牌，放在机密 CF_RADAR_TOKEN。"""
    tok = os.environ.get("CF_RADAR_TOKEN")
    if not tok:
        items.append({"t": iso(NOW), "src": "Cloudflare Radar", "kind": "MISSING", "text": "需要 Cloudflare API 令牌（未配置）", "text_en": "Needs a Cloudflare API token (not configured)"}); return
    H = {"authorization": "Bearer " + tok}; a, b = iso(t0 - timedelta(days=1)), iso(min(NOW, t0 + timedelta(days=2)))
    try:
        n = 0
        for path, name in (("annotations/outages", "中断记录"), ("traffic_anomalies", "流量异常")):
            x = get(f"https://api.cloudflare.com/client/v4/radar/{path}?location={cty(ev)[2]}&dateStart={a}&dateEnd={b}&format=json&limit=20", headers=H)
            r = x.get("result", {}); L = r.get("annotations") or r.get("trafficAnomalies") or []
            for o in L:
                n += 1; t = o.get("startDate") or o.get("startDate")
                items.append({"t": (t or a)[:19] + "Z", "src": "Cloudflare Radar", "kind": "SUPPORTING", "text": f"{cty(ev)[1]}{name}：{o.get('description') or o.get('outage', {}).get('outageCause') or o.get('type', '')}",
                              "text_en": f"{cty(ev)[0]} {'outage' if 'outage' in path else 'traffic anomaly'}: {o.get('description') or o.get('outage', {}).get('outageCause') or o.get('type', '')}"})
        if not n:
            items.append({"t": iso(t0), "src": "Cloudflare Radar", "kind": "NEUTRAL", "text": f"事件前后没有{cty(ev)[1]}网络中断或流量异常记录", "text_en": f"No {cty(ev)[0]} outage or traffic anomaly recorded around the event"})
    except Exception as e:
        items.append({"t": iso(t0), "src": "Cloudflare Radar", "kind": "MISSING", "text": f"查询失败（{str(e)[:60]}）", "text_en": f"Query failed ({str(e)[:60]})"})


def firms(ev, t0, items, pack):
    """NASA FIRMS 卫星火点（VIIRS）：事件 25 km 内前后各 5 天。需要免费 MAP_KEY，放在机密 FIRMS_MAP_KEY。"""
    key = os.environ.get("FIRMS_MAP_KEY")
    if not key:
        items.append({"t": iso(NOW), "src": "NASA FIRMS 火点", "kind": "MISSING", "text": "需要 FIRMS MAP_KEY（未配置）", "text_en": "Needs a FIRMS MAP_KEY (not configured)"}); return
    bb = f"{ev['lon'] - 0.25:.3f},{ev['lat'] - 0.25:.3f},{ev['lon'] + 0.25:.3f},{ev['lat'] + 0.25:.3f}"
    try:
        cnt = {"before": 0, "after": 0}; first = None
        for src in ("VIIRS_SNPP_NRT", "VIIRS_NOAA20_NRT"):
            for which, day in (("before", (t0 - timedelta(days=5)).strftime("%Y-%m-%d")), ("after", t0.strftime("%Y-%m-%d"))):
                txt = get(f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{key}/{src}/{bb}/5/{day}", raw=True, timeout=60).decode()
                rows = [r.split(",") for r in txt.strip().splitlines()[1:] if r]
                cnt[which] += len(rows)
                if which == "after":
                    for r in rows:
                        t = f"{r[5]}T{r[6].zfill(4)[:2]}:{r[6].zfill(4)[2:]}:00Z"
                        if first is None or t < first: first = t
        pack["firms"] = cnt
        items.append({"t": first or iso(t0), "src": "NASA FIRMS 火点", "kind": "SUPPORTING" if cnt["after"] > cnt["before"] + 3 else "NEUTRAL",
                      "text": f"事件 25 km 内卫星火点：事件前 5 天 {cnt['before']} 个，之后 5 天 {cnt['after']} 个", "text_en": f"Satellite fire detections within 25 km: {cnt['before']} in the 5 days before, {cnt['after']} in the 5 days after"})
    except Exception as e:
        items.append({"t": iso(t0), "src": "NASA FIRMS 火点", "kind": "MISSING", "text": f"查询失败（{str(e)[:60]}）", "text_en": f"Query failed ({str(e)[:60]})"})


def blackmarble(ev, t0, items, pack):
    """NASA Black Marble 每日夜光（VNP46A2）：事件 10 km 内灯光亮度，事件前 7 天中位数和之后每天比较，看是否停电。
    检索不需要账号；下载需要 Earthdata 令牌，放在机密 EARTHDATA_TOKEN。"""
    tok = os.environ.get("EARTHDATA_TOKEN")
    if not tok:
        items.append({"t": iso(NOW), "src": "NASA 夜间灯光", "kind": "MISSING", "text": "需要 NASA Earthdata 账号令牌（未配置）", "text_en": "Needs a NASA Earthdata token (not configured)"}); return
    try:
        import h5py, io, numpy as np
        bb = f"{ev['lon'] - 0.1},{ev['lat'] - 0.1},{ev['lon'] + 0.1},{ev['lat'] + 0.1}"
        x = get("https://cmr.earthdata.nasa.gov/search/granules.json?" + urllib.parse.urlencode({"short_name": "VNP46A2", "bounding_box": bb, "temporal": f"{iso(t0 - timedelta(days=8))},{iso(min(NOW, t0 + timedelta(days=5)))}", "page_size": 20, "sort_key": "start_date"}))
        vals = []
        for g in x.get("feed", {}).get("entry", []):
            href = next((l["href"] for l in g.get("links", []) if l.get("href", "").endswith(".h5") and l["href"].startswith("https")), None)
            if not href: continue
            b = get(href, raw=True, timeout=180, headers={"authorization": "Bearer " + tok})
            f = h5py.File(io.BytesIO(b), "r"); grp = f["HDFEOS/GRIDS/VNP_Grid_DNB/Data Fields"]
            arr = grp["DNB_BRDF-Corrected_NTL"][:].astype(float); fill = grp["DNB_BRDF-Corrected_NTL"].attrs.get("_FillValue", [65535])[0]
            h, v = re.search(r"h(\d\d)v(\d\d)", href).groups(); lon0 = -180 + int(h) * 10; lat0 = 90 - int(v) * 10
            r0 = int((lat0 - (ev["lat"] + 0.1)) / (10 / 2400)); r1 = int((lat0 - (ev["lat"] - 0.1)) / (10 / 2400)); c0 = int((ev["lon"] - 0.1 - lon0) / (10 / 2400)); c1 = int((ev["lon"] + 0.1 - lon0) / (10 / 2400))
            sub = arr[max(0, r0):r1, max(0, c0):c1]; sub = sub[sub != fill]
            if sub.size: vals.append((g["time_start"][:10], float(np.nanmean(sub)) * 0.1))
        pre = [v for d, v in vals if d < t0.strftime("%Y-%m-%d")]; post = [(d, v) for d, v in vals if d >= t0.strftime("%Y-%m-%d")]
        pack["blackmarble"] = vals
        if pre and post:
            base = float(np.median(pre)); low = min(post, key=lambda z: z[1])
            drop = base > 0 and low[1] < 0.6 * base
            items.append({"t": low[0] + "T20:00:00Z", "src": "NASA 夜间灯光", "kind": "SUPPORTING" if drop else "NEUTRAL",
                          "text": f"事件 10 km 内夜间灯光：事件前中位数 {base:.1f}，之后最低 {low[1]:.1f}（{low[0]}）" + ("，明显变暗，可能停电" if drop else ""),
                          "text_en": f"Night lights within 10 km: median before {base:.1f}, lowest after {low[1]:.1f} ({low[0]})" + (", clearly darker, possible outage" if drop else "")})
        else:
            items.append({"t": iso(NOW), "src": "NASA 夜间灯光", "kind": "MISSING", "text": "夜光数据还不够（产品滞后几天，或被云遮挡）", "text_en": "Not enough night-light data yet (product lags a few days, or cloud)"})
    except Exception as e:
        items.append({"t": iso(t0), "src": "NASA 夜间灯光", "kind": "MISSING", "text": f"处理失败（{str(e)[:60]}）", "text_en": f"Processing failed ({str(e)[:60]})"})


def gnss(ev, t0, items, pack):
    """内华达大学 NGL 的 GNSS 每日解算：只在事件 150 km 内有 M5 以上地震时看，事件前后 5 天平均位置差。"""
    if not any(i["src"] == "USGS 地震目录" and re.match(r"M([5-9])", i.get("text", "")) for i in items):
        return
    try:
        txt = get("https://geodesy.unr.edu/NGLStationPages/DataHoldings.txt", raw=True, timeout=120).decode(errors="ignore")
        cands = []
        for ln in txt.splitlines()[1:]:
            c = ln.split()
            try:
                la, lo = float(c[1]), float(c[2]); lo = lo - 360 if lo > 180 else lo
            except Exception:
                continue
            d = km((ev["lat"], ev["lon"]), (la, lo))
            if d <= 150: cands.append((d, c[0]))
        cands.sort(); out = []
        for d, sta in cands[:3]:
            series = None
            for u in (f"https://geodesy.unr.edu/gps_timeseries/rapids/tenv3/IGS20/{sta}.tenv3", f"https://geodesy.unr.edu/gps_timeseries/IGS20/tenv3/IGS20/{sta}.tenv3", f"https://geodesy.unr.edu/gps_timeseries/tenv3/IGS14/{sta}.tenv3"):
                try: series = get(u, raw=True, timeout=60).decode(); break
                except Exception: continue
            if not series: continue
            rows = []
            for ln in series.splitlines()[1:]:
                c = ln.split()
                try: rows.append((datetime.strptime(c[1], "%y%b%d").replace(tzinfo=timezone.utc), float(c[8]) + float(c[7]), float(c[10]) + float(c[9]), float(c[12])))
                except Exception: continue
            pre = [r for r in rows if t0 - timedelta(days=6) <= r[0] < t0]; post = [r for r in rows if t0 < r[0] <= t0 + timedelta(days=6)]
            if pre and post:
                m = lambda L, i: sum(r[i] for r in L) / len(L)
                de, dn, du = [(m(post, i) - m(pre, i)) * 1000 for i in (1, 2, 3)]
                out.append(sta)
                items.append({"t": iso(post[0][0]), "src": "GNSS 测站", "kind": "SUPPORTING" if (de * de + dn * dn) ** 0.5 > 10 else "NEUTRAL",
                              "text": f"{sta}（距约 {d:.0f} km）事件前后 5 天平均位置变化：东 {de:+.0f} mm、北 {dn:+.0f} mm、垂直 {du:+.0f} mm",
                              "text_en": f"{sta} (about {d:.0f} km): mean position change over 5 days before/after: east {de:+.0f} mm, north {dn:+.0f} mm, up {du:+.0f} mm"})
            else:
                items.append({"t": iso(NOW), "src": "GNSS 测站", "kind": "MISSING", "text": f"{sta}（距约 {d:.0f} km）事件后的解算还没出（通常滞后几天到两周）", "text_en": f"{sta} (about {d:.0f} km): post-event solutions not out yet (usually days to two weeks)"})
        pack["gnss"] = {"stations": [c[1] for c in cands[:3]]}
        if not cands:
            items.append({"t": iso(t0), "src": "GNSS 测站", "kind": "MISSING", "text": "事件 150 km 内没有公开 GNSS 站", "text_en": "No public GNSS station within 150 km"})
    except Exception as e:
        items.append({"t": iso(t0), "src": "GNSS 测站", "kind": "MISSING", "text": f"查询失败（{str(e)[:60]}）", "text_en": f"Query failed ({str(e)[:60]})"})


def spaceweather(ev, t0, items, pack):
    """太阳活动 / 地磁暴（GFZ Kp 指数）：作为背景记录。地磁暴会影响 GNSS 定位、卫星通信和短波电台，可用来解释同时段的通信或定位异常。"""
    try:
        x = get("https://kp.gfz-potsdam.de/app/json/?" + urllib.parse.urlencode({"start": iso(t0 - timedelta(days=1)), "end": iso(min(NOW, t0 + timedelta(days=1))), "index": "Kp"}))
        L = list(zip(x.get("datetime", []), x.get("Kp", [])))
        if not L: raise RuntimeError("没有数据")
        t, k = max(L, key=lambda z: z[1]); pack["kp_max"] = k
        items.append({"t": t[:19] + "Z", "src": "地磁 Kp（GFZ）", "kind": "NEUTRAL",
                      "text": f"事件前后一天最大 Kp {k:.1f}" + ("：有地磁暴，同时段 GNSS 和卫星通信可能受影响" if k >= 5 else "：没有地磁暴"),
                      "text_en": f"Max Kp {k:.1f} within a day of the event" + (": geomagnetic storm; GNSS and satellite links may have been affected" if k >= 5 else ": no geomagnetic storm")})
    except Exception as e:
        items.append({"t": iso(t0), "src": "地磁 Kp（GFZ）", "kind": "MISSING", "text": f"查询失败（{str(e)[:60]}）", "text_en": f"Query failed ({str(e)[:60]})"})


def who_don(ev, t0, items, pack):
    """世卫组织疫情通报（Disease Outbreak News）：事件前后 60 天内提到尼泊尔或中国的通报。只对疫情类事件运行。"""
    try:
        x = get("https://www.who.int/api/news/diseaseoutbreaknews?" + urllib.parse.urlencode({"sf_culture": "en", "$orderby": "PublicationDateAndTime desc", "$top": 50}))
        hits = []
        for r in x.get("value", []):
            t = (r.get("PublicationDateAndTime") or r.get("PublicationDate") or "")[:19]
            if not t or abs((P(t + "Z") - t0).days) > 60: continue
            if re.search(r"Nepal|China|India|Bhutan", r.get("Title", "") or ""):
                hits.append(r)
        for r in hits[:5]:
            items.append({"t": r["PublicationDateAndTime"][:19] + "Z", "src": "WHO 疫情通报", "kind": "SUPPORTING", "text": r["Title"], "text_en": r["Title"],
                          "url": "https://www.who.int/emergencies/disease-outbreak-news/item/" + (r.get("UrlName") or "")})
        if not hits:
            items.append({"t": iso(t0), "src": "WHO 疫情通报", "kind": "NEUTRAL", "text": "前后 60 天没有涉及尼泊尔及周边的世卫组织疫情通报", "text_en": "No WHO Disease Outbreak News for Nepal or neighbours within 60 days"})
    except Exception as e:
        items.append({"t": iso(t0), "src": "WHO 疫情通报", "kind": "MISSING", "text": f"查询失败（{str(e)[:60]}）", "text_en": f"Query failed ({str(e)[:60]})"})


_HZREC = None


def hazard_records(ev, t0, items, pack):
    """灾种扫描（hazards/records.json，281 种灾害、20 多个公开来源，每小时更新）里，事件 150 km 内、前 1 天到后 5 天的记录挂到时间线上。
    没有坐标的新闻，标题里要出现事件所在地名。"""
    global _HZREC
    if _HZREC is None:
        try: _HZREC = json.load(open("hazards/records.json")).get("records", [])
        except Exception: _HZREC = []
    a, b = t0 - timedelta(days=1), t0 + timedelta(days=5)
    place = (ev.get("district") or place_word(ev) or "").lower()
    skip = {"USGS 地震目录", "GDACS", "BIPAD 警报"}   # 证据包里已经单独查过
    hits = []
    for r in _HZREC:
        if r.get("src") in skip or not r.get("t"): continue
        try: tr = P(r["t"])
        except Exception: continue
        if not (a <= tr <= b): continue
        if r.get("lat") is not None and r.get("lon") is not None:
            if km((ev["lat"], ev["lon"]), (r["lat"], r["lon"])) > 150 or r.get("observation"): continue
        elif not (r.get("news") and place and place != "nepal" and place in r.get("title", "").lower()):
            continue
        hits.append(r)
    fam = {c[:2] for c in (ev.get("hips") or [])}
    def score(r):   # 伤亡多、同一大类、离得近、新闻点名本地的优先
        d = km((ev["lat"], ev["lon"]), (r["lat"], r["lon"])) if r.get("lat") is not None else 60
        return ((r.get("deaths") or 0) + (r.get("missing") or 0)) * 10 + (5 if fam & {c[:2] for c in r.get("codes", [])} else 0) + (3 if d < 30 else 1 if d < 80 else 0) + (4 if r.get("news") else 0)
    top = sorted(hits, key=score, reverse=True)[:25]
    top.sort(key=lambda r: r["t"])
    for r in top:
        extra = (f"（死亡 {r['deaths']}" + (f"、失踪 {r['missing']}" if r.get("missing") else "") + "）") if r.get("deaths") else (f"（失踪 {r['missing']}）" if r.get("missing") else "")
        items.append({"t": r["t"], "src": "灾种扫描 · " + r["src"], "kind": "SUPPORTING", "hips": r.get("codes", []),
                      "text": r["title"] + extra, "text_en": r["title"] + extra, "url": r.get("url")})
    pack["hazard_links"] = {"n": len(hits), "codes": sorted({c for r in hits for c in r.get("codes", [])})}


_VANTOR = []


def vantor(ev, t0, items, pack):
    """Vantor（原 Maxar）开放数据：重大灾害后公开的高分辨率灾前灾后影像（CC BY 4.0），看有没有覆盖这次事件。"""
    try:
        if not _VANTOR:   # 目录只取一次，各事件共用
            cat = get("https://vantor-opendata.s3.amazonaws.com/events/catalog.json")
            for l in cat.get("links", []):
                if l.get("rel") != "child": continue
                href = urllib.parse.urljoin("https://vantor-opendata.s3.amazonaws.com/events/catalog.json", l["href"])
                try: _VANTOR.append((href, get(href, timeout=30)))
                except Exception: continue
        hits = []
        for href, c in _VANTOR:
            bb = ((c.get("extent") or {}).get("spatial") or {}).get("bbox") or [[]]
            tt = ((c.get("extent") or {}).get("temporal") or {}).get("interval") or [[None, None]]
            for b4 in bb:
                if len(b4) >= 4 and b4[0] - 0.5 <= ev["lon"] <= b4[2] + 0.5 and b4[1] - 0.5 <= ev["lat"] <= b4[3] + 0.5:
                    # 要有事件之后拍的影像才算：用目录的最晚拍摄时间；没有结束时间的，看名字里的年月是不是事件当月
                    t1 = tt[0][1]; nm = (c.get("title") or c.get("id") or "")
                    if (t1 and P(t1) >= t0 and P(t1) <= t0 + timedelta(days=60)) or (not t1 and t0.strftime("%b") in nm and str(t0.year) in nm):
                        hits.append((nm, href, t1 or iso(t0))); break
        for h in hits:
            items.append({"t": (h[2] or iso(t0))[:19] + "Z", "src": "Vantor 开放影像", "kind": "SUPPORTING", "text": f"高分辨率开放影像覆盖本地：{h[0]}", "text_en": f"Open high-resolution imagery covers this area: {h[0]}",
                          "url": "https://radiantearth.github.io/stac-browser/#/external/" + h[1].replace("https://", "")})
        if not hits:
            items.append({"t": iso(NOW), "src": "Vantor 开放影像", "kind": "NEUTRAL", "text": "这次事件没有启动开放影像", "text_en": "No open imagery released for this event"})
    except Exception as e:
        items.append({"t": iso(NOW), "src": "Vantor 开放影像", "kind": "MISSING", "text": f"查询失败（{str(e)[:60]}）", "text_en": f"Query failed ({str(e)[:60]})"})


GDACS_HIPS = {"EQ": "GH0101", "FL": "MH0600", "TC": "MH0309", "DR": "MH0401", "WF": "EN0205", "VO": "GH0200"}


_GLOF = None
GLOF_REPO = "fidelsteiner/HMAGLOFDB"
GLOF_FILE = "Database/GLOFs/HMAGLOFDB.csv"


def glof_db():
    """高山亚洲冰湖溃决数据库（Steiner & Shrestha，ICIMOD / 乌得勒支大学；ESSD 2023, doi:10.5194/essd-15-3941-2023）。
    读 GitHub 上滚动更新的开发版（新事件核对后先进这里，再发 Zenodo 正式版），每次生成证据包现取，记下当时的提交号。
    已被作者判为可疑或不是冰湖溃决的条目在另一个文件（HMAGLOFDB_removed.csv），这里不读。"""
    global _GLOF
    if _GLOF is not None: return _GLOF
    import csv, io
    _GLOF = {"rows": [], "src": None}
    tok = os.environ.get("GITHUB_TOKEN")
    try:
        c = get(f"https://api.github.com/repos/{GLOF_REPO}/commits?path={GLOF_FILE}&per_page=1", headers={"authorization": f"Bearer {tok}"} if tok else None)[0]
        sha, when = c["sha"], c["commit"]["committer"]["date"]
    except Exception:
        sha, when = "main", None
    txt = get(f"https://raw.githubusercontent.com/{GLOF_REPO}/{sha}/{GLOF_FILE}", raw=True, timeout=60).decode("utf-8", "ignore")
    for r in csv.DictReader(io.StringIO(txt)):
        r = {k: ("" if (v or "").strip() in ("NA", "NaN", "nan", "-") else (v or "").strip()) for k, v in r.items()}
        def f(k):
            try: return float(r.get(k) or "nan")
            except ValueError: return float("nan")
        la, lo = f("Lat_impact"), f("Lon_impact")
        if la != la: la, lo = f("Lat_lake"), f("Lon_lake")
        if la != la or lo != lo: continue
        y = (r.get("Year_exact") or "").strip()
        _GLOF["rows"].append({"id": r.get("GF_ID"), "year": y or (r.get("Year_approx") or "").strip(), "exact": bool(y),
                              "month": (r.get("Month") or "").strip(), "day": (r.get("Day") or "").strip(),
                              "lake": (r.get("Lake_name") or r.get("GL_ID") or "").strip(), "country": (r.get("Country") or "").strip(),
                              "lat": la, "lon": lo, "lat_lake": f("Lat_lake"), "lon_lake": f("Lon_lake"),
                              "lives": (r.get("Lives_total") or "").strip(), "mechanism": (r.get("Mechanism") or "").strip(),
                              "ref": (r.get("Ref_scientific") or r.get("Ref_other") or "").strip()[:160]})
    _GLOF["src"] = {"name": "HMAGLOFDB（高山亚洲冰湖溃决数据库）", "repo": f"https://github.com/{GLOF_REPO}", "commit": sha, "commit_time": when,
                    "file": f"https://github.com/{GLOF_REPO}/blob/{sha}/{GLOF_FILE}", "release_doi": "https://doi.org/10.5281/zenodo.7271187",
                    "paper": "https://doi.org/10.5194/essd-15-3941-2023", "n": len(_GLOF["rows"]), "fetched": iso(NOW)}
    return _GLOF


def glof_history(ev, t0, items, pack):
    """冰湖溃决数据库：①事件前 1 天到后 5 天、80 km 内有收录的溃决 → 进时间线（支持）；
    ②事件 30 km 内历史上收录过的溃决 → pack["history"]，只是数据库记录（带出处），不是这次事件的证据，不进时间线。"""
    if not (25 <= ev["lat"] <= 50 and 60 <= ev["lon"] <= 105): return
    try:
        db = glof_db()
    except Exception as e:
        items.append({"t": iso(NOW), "src": "冰湖溃决数据库", "kind": "MISSING", "text": f"读取失败（{str(e)[:60]}）", "text_en": f"Fetch failed ({str(e)[:60]})"}); return
    def dist(r):
        d = km((ev["lat"], ev["lon"]), (r["lat"], r["lon"]))
        if r["lat_lake"] == r["lat_lake"]: d = min(d, km((ev["lat"], ev["lon"]), (r["lat_lake"], r["lon_lake"])))
        return d
    a, b = t0 - timedelta(days=1), t0 + timedelta(days=5)
    hist = []
    for r in db["rows"]:
        d = dist(r)
        if d > 80: continue
        when = None
        if r["exact"] and r["month"] and r["day"]:
            try: when = datetime(int(float(r["year"])), int(float(r["month"])), int(float(r["day"])), tzinfo=timezone.utc)
            except ValueError: when = None
        lives = f"，死亡 {r['lives']}" if r["lives"] and r["lives"] not in ("0", "NA", "nan") else ""
        if when and a <= when <= b:
            items.append({"t": iso(when), "src": "冰湖溃决数据库 HMAGLOFDB", "kind": "SUPPORTING", "hips": ["MH0607"],
                          "text": f"数据库收录：{r['lake'] or '未命名冰湖'} 溃决（{r['country']}，距事件 {d:.0f} km{lives}；编号 {r['id']}）",
                          "text_en": f"Database record: outburst of {r['lake'] or 'unnamed lake'} ({r['country']}, {d:.0f} km; ID {r['id']})",
                          "url": db["src"]["file"]})
        elif d <= 30:
            hist.append({"id": r["id"], "year": r["year"], "date": "-".join(x for x in (r["year"], r["month"], r["day"]) if x) if r["exact"] else (f"约 {r['year']}" if r["year"] else "年份不详"),
                         "lake": r["lake"], "country": r["country"], "km": round(d, 1), "lives": r["lives"] or None, "mechanism": r["mechanism"] or None, "ref": r["ref"] or None})
    if hist:
        hist.sort(key=lambda h: (h["year"] != "", str(h["year"])), reverse=True)
        pack["history"] = {"source": db["src"], "radius_km": 30, "n": len(hist), "records": hist[:20],
                           "note": "数据库里事件 30 km 内历史上收录过的冰湖溃决，每条带数据库编号和原始文献；只是历史记录，不是这次事件的证据，也不用来推测。"}


# 推断边界：每类来源的记录“能说明什么、不能说明什么”。数据的局限是推断的边界，不是丢掉数据的理由。
# 按时间线条目的来源名前缀匹配；证据包里只放这次用到的来源。
BOUNDS = [
    ("IO.EVN 地震台", "台站在这一时刻记录到的地面震动强弱（1–5 Hz，相对自身背景）；有数据缺口时说明台站或传输中断。",
     "不能说明震动的来源（滑坡、雪崩、冰崩、地震、风、人为活动都可能）和发生地点；单台不能定位。"),
    ("KKN 地震台", "同上：台站记录到的震动强弱和数据缺口。和 IO.EVN 对照，可以看信号是局部的还是区域性的。",
     "不能说明来源和地点；两台都没有记录不等于没有发生（离得远、频段不同都可能漏掉）。"),
    ("Raspberry Shake", "民间地震仪在这一时刻是否记录到震动、有没有在线。", "民用设备，噪声大、没有官方校准；不能单独说明发生了什么。"),
    ("USGS 地震目录", "USGS 测定的地震（或崩塌类事件）的时间、位置、震级。", "目录里的位置和震级会修订；崩塌类事件的位置不精确；不说明是否造成损失。"),
    ("EMSC 地震目录", "EMSC 汇总的地震时间、位置、震级。", "早期结果会修订；不说明影响和损失。"),
    ("USGS ShakeMap", "USGS 按模型和观测估算的地面震动分布。", "是模型估计，不是实测；不说明具体建筑或地点的损毁。"),
    ("USGS 有感报告", "公众提交的“有感”报告数量和分布。", "自愿提交，有人口和网络偏差；没有报告不等于无感。"),
    ("USGS PAGER", "USGS 按模型估算的伤亡和经济损失等级。", "是模型估计，不是统计结果；不能当作实际伤亡数。"),
    ("GNSS 测站", "测站坐标在事件前后的变化。", "毫米级变化受季节、设备影响；不能单独说明地表破坏。"),
    ("BIPAD 水位站", "附近水位站在报还是停报、最后一次数据时间。", "停报可能是洪水冲毁，也可能是断电、通信或维护；不能说明原因。"),
    ("BIPAD 灾害警报", "尼泊尔政府系统在这一时刻发出了这条警报。", "警报不等于灾害已经发生；不说明影响范围。"),
    ("BIPAD 灾害事件库", "尼泊尔政府登记的事件、时间、地点和伤亡数字。", "登记有延迟，数字会更新；地点通常只到村镇一级。"),
    ("哥白尼 GFM", "哥白尼全球洪水监测按 Sentinel-1 雷达自动算出的水体范围。", "自动产品，山区阴影、积雪、植被会误判或漏判；不说明水深和损失。"),
    ("Sentinel-1 雷达", "这一时间有没有雷达影像覆盖事件地点，可用于前后对比。", "有影像不等于能看出变化；山区几何畸变严重，需人工判读。"),
    ("Sentinel-2 光学", "这一时间有没有光学影像覆盖、云量多少，可用于前后对比。", "云和阴影会遮挡；有影像不等于能看出变化。"),
    ("Copernicus EMS", "欧盟应急制图服务是否为这次事件启动、出了哪些图。", "没启动不说明灾害小；图是对某一时刻的判读。"),
    ("Vantor 开放影像", "是否为这次事件公开了高分辨率影像。", "只说明有没有影像，不说明影像里看到了什么。"),
    ("IODA 网络连通", "当地网络连通指标在这一时刻是否下降。", "下降可能是断电、线路损坏，也可能是运营商维护；不能说明原因。"),
    ("Cloudflare Radar", "Cloudflare 观测到的当地网络流量或中断。", "只反映经过 Cloudflare 的流量；不能说明原因。"),
    ("NASA FIRMS", "卫星在过境时探测到的热异常（火点）。", "云遮挡会漏检；热异常可能是农业烧荒、工业热源；不说明起火原因。"),
    ("NASA 夜间灯光", "夜间灯光亮度在事件前后的变化。", "受云、月光、季节影响；变暗不一定是停电。"),
    ("地磁 Kp", "这段时间的地磁活动水平，作为 GNSS 和卫星通信的背景。", "和地面灾害没有因果关系；只用来说明观测条件。"),
    ("IFRC Montandon", "国际红十字会 Montandon 库里有没有这次事件的记录。", "收录有延迟；没收录不说明没发生。"),
    ("ReliefWeb", "联合国人道机构网站上关于这次事件的报告。", "报告引用的数字来自各方，会更新；不同报告可能不一致。"),
    ("OCHA HDX", "人道数据交换平台上有没有相关数据集。", "只说明有数据集，不说明其内容是否准确。"),
    ("GDELT 新闻", "全球新闻里有没有报道、报道的数量和时间。", "新闻是二手信息，早期报道常有误；报道多少不等于事件大小。"),
    ("维基百科", "有没有人为这次事件新建或编辑条目。", "任何人可编辑；只说明受到关注，不是事实来源。"),
    ("WHO 疫情通报", "世卫组织发布的疫情通报内容和时间。", "通报基于各国上报，有延迟；数字会更新。"),
    ("GDACS", "联合国和欧盟的全球灾害预警系统给出的事件和级别。", "级别是按模型估算的影响，不是实际损失。"),
    ("冰湖溃决数据库", "高山亚洲冰湖溃决数据库里收录的溃决记录（带编号和文献）。", "收录依赖已有报道和影像；没有收录不说明没发生过。"),
    ("人工提交", "有人在这个时间提交了这份材料，其指纹（SHA-256）在存证时已经存在。", "提交不等于内容真实；只有所有者核实“已采信”后才进入公开时间线。"),
    ("灾种扫描", "这个公开来源在这一时间发布了这条记录。", "只是记录本身；不同来源的同一事件可能重复，数字以原始来源为准。"),
]


def bounds_of(src):
    for k, can, cannot in BOUNDS:
        if src.startswith(k) or (k == "灾种扫描" and src.startswith("灾种扫描")):
            return k, can, cannot
    return None


def add_bounds(pack):
    used = {}
    for it in pack.get("timeline", []):
        b = bounds_of(it.get("src", ""))
        if b:
            it["bound"] = b[0]
            used[b[0]] = {"can": b[1], "cannot": b[2]}
    pack["bounds"] = used


_VEN = None


def references(pack):
    """按事件的灾害编码，从 hazards/venues.json（281 灾种期刊排名，OpenAlex）挂上该灾种的数据论文和专业期刊，作为背景引用。
    只是“这类灾害可参考的公开数据和文献”，不是这次事件的证据，不进时间线。"""
    global _VEN
    if _VEN is None:
        try: _VEN = {h["code"]: h for h in json.load(open("hazards/venues.json"))["hazards"] if h and not h.get("err")}
        except Exception: _VEN = {}
    refs = []
    for c in (pack.get("hips") or [])[:3]:
        h = _VEN.get(c)
        if not h: continue
        refs.append({"hips": c, "hazard": h.get("label_zh"), "query": h.get("query"),
                     "data_papers": [{k: x.get(k) for k in ("title", "doi", "journal", "year")} for x in h.get("data_papers", [])
                                     if any(w[:5] in (x.get("title") or "").lower() for w in re.split(r"[^a-z0-9]+", (h.get("query") or "").lower()) if len(w) >= 4)],
                     "venues": [{"name": v.get("name"), "h": v.get("h")} for v in h.get("top_venues", [])]})
    if refs:
        pack["references"] = refs
        pack["references_note"] = "该灾种可引用的公开数据论文和专业期刊（OpenAlex 自动检索，见 docs/HAZARD_VENUES.md），是背景参考，不是本次事件的证据。"


def hips_of(ev):
    """事件的联合国减灾署 2025 灾害编码；Worker 还没补上时按编号推断。"""
    if ev.get("hips"): return ev["hips"]
    m = re.match(r"gdacs-(\w+)-", ev["id"])
    if m: return [GDACS_HIPS.get(m.group(1), "MH0600")]
    if ev["id"].startswith("usgs-"): return ["GH0101" if ev.get("kind") == "地震" else "GH0300"]
    return ["MH0604"]


# 10-18（用户要求）：事件时间以数据源为准，不用我们发现事件、更新证据包的时间。
# 取时间线里最早的一条一手记录：发现事件时的来源记录（BIPAD 警报/事件库、USGS、GDACS、水位站、新闻）；
# 新闻线索类再加上灾种扫描里同灾种的新闻（只看发现日之前 3 天以内的，避免把无关的旧报道算进来）。
# 来源只给到日期的（BIPAD 事件库是尼泊尔当地零点 = UTC 18:15，GDELT 有时是 UTC 零点）标 t_prec = "day"，页面只显示日期。
def source_time(ev, pack, items):
    det = P(ev["t"]); lo = iso(det - timedelta(days=3)); hi = iso(NOW); hz = set(pack.get("hips") or [])
    # 一手记录 = 发现这个事件时的来源记录本身。新闻线索类事件（news-）另外算上灾种扫描里同灾种的新闻 RSS（同一批报道，常常比 GDELT 收录得早）；
    # 别的事件不算灾种扫描的附近记录——那是附近的其他事件，不是这一起。
    news = ev["id"].startswith("news-")
    cand = [i for i in items if i.get("kind") == "SUPPORTING" and i["t"] <= hi and (
        i.get("primary") or (news and lo <= i["t"] and i.get("src") == "灾种扫描 · 新闻 RSS" and hz & set(i.get("hips") or [])))]
    pack["t_detected"] = ev["t"]
    if not cand:
        pack["t_src"] = "发现事件的时间（没有更早的一手记录）"; return
    first = min(cand, key=lambda i: i["t"])
    pack["t"] = first["t"]; pack["t_src"] = first["src"]
    if first["t"][10:19] in ("T00:00:00", "T18:15:00"): pack["t_prec"] = "day"


def build(ev):
    ev["hips"] = hips_of(ev)
    t0 = P(ev["t"]); items = []
    m = re.search(r"bipad-([a-z-]+)-\d{4}", ev["id"])
    if m:
        ev["district"] = next((d for d in DIST if d.lower() == m.group(1).replace("-", " ") or d.lower() == m.group(1)), None)
    for s in ev.get("src", []):
        items.append({"t": s["t"], "src": s["src"], "kind": "SUPPORTING", "text_en": s.get("text_en", s["text"]), "text": s["text"], "url": s.get("url"), "primary": True})
    pack = {"id": ev["id"], "hips": ev.get("hips") or [], "title": ev["title"], "title_en": ev.get("title_en") or ev["title"].replace("洪水预警", "flood warning"), "kind": ev.get("kind"), "place": ev.get("place"), "lat": ev["lat"], "lon": ev["lon"], "t": ev["t"]}
    bio = (ev.get("hips") or []) and all(c.startswith("BI") for c in ev["hips"])
    if bio:   # 疫情：地震台、水位、卫星这些物理信号不相关，只查新闻、公开记录和世卫通报
        fns = (lambda: gdelt(ev, t0, items, pack), lambda: wiki(ev, t0, items, pack), lambda: hdx(ev, t0, items, pack), lambda: reliefweb(ev, t0, items, pack),
               lambda: who_don(ev, t0, items, pack), lambda: manual(ev, t0, items, pack), lambda: hazard_records(ev, t0, items, pack))
    for fn in fns if bio else (lambda: evn(ev, t0, items, pack), lambda: kkn(ev, t0, items, pack), lambda: catalogs(ev, t0, items), lambda: gauges(ev, t0, items, pack),
               lambda: ioda(ev, t0, items, pack), lambda: ems(ev, t0, items), lambda: sentinel(ev, t0, items, pack),
               lambda: gfm(ev, t0, items, pack), lambda: montandon(ev, t0, items, pack), lambda: manual(ev, t0, items, pack),
               lambda: rshake(ev, t0, items, pack), lambda: usgs_products(ev, t0, items, pack), lambda: gnss(ev, t0, items, pack),
               lambda: gdelt(ev, t0, items, pack), lambda: wiki(ev, t0, items, pack), lambda: hdx(ev, t0, items, pack), lambda: reliefweb(ev, t0, items, pack),
               lambda: cfradar(ev, t0, items, pack), lambda: firms(ev, t0, items, pack), lambda: blackmarble(ev, t0, items, pack),
               lambda: spaceweather(ev, t0, items, pack), lambda: vantor(ev, t0, items, pack), lambda: hazard_records(ev, t0, items, pack),
               lambda: glof_history(ev, t0, items, pack)):
        try:
            fn()
        except Exception:
            traceback.print_exc()
    try:
        plot_seis(ev, t0, pack)
    except Exception:
        traceback.print_exc()
    pack.pop("_series_evn", None); pack.pop("_series_kkn", None); pack.pop("_evn_gaps", None)
    try:
        references(pack)
    except Exception:
        traceback.print_exc()
    items.sort(key=lambda i: i["t"])
    source_time(ev, pack, items)
    for i in items: i.pop("primary", None)
    pack["timeline"] = items; pack["built"] = iso(NOW)
    add_bounds(pack)
    try:
        wayback_attach(pack)
    except Exception:
        traceback.print_exc()
    pack["note_en"] = "States only what public sources recorded and when; no attribution of cause, no prediction. A strong seismic signal only means the station recorded strong shaking at that moment."
    pack["note"] = "只陈述公开来源记录了什么、什么时候；不判断成因，不预测。地震台强信号只说明那一刻台站记录到较强震动，来源需要结合其他证据。"
    return pack



# 互联网档案馆时光机（Wayback Machine）存档：证据包里每条“支持 / 矛盾”记录的原始网页，用公开的“立即保存”（Save Page Now）
# 请时光机存一份，存档地址写进时间线条目（archive / archive_t）。原网页以后被改或被删，时光机里那一刻的样子还在；
# 存档由独立第三方保存，和本平台的比特币时间戳、RFC 3161、Sigstore 互相印证。每个网址只存一次（events/wayback.json 记账）。
WAYBACK_DB = os.path.join(OUT, "wayback.json")
WAYBACK_BUDGET = [int(os.environ.get("WAYBACK_BUDGET", "10"))]   # 每次运行最多新存几个（匿名接口有频率限制）
WAYBACK_DEADLINE = [time.time() + 8 * 60]   # 整次运行花在存档上的时间不超过 8 分钟，超了留到下次


def wayback_save(url):
    import time as _t
    req = urllib.request.Request("https://web.archive.org/save/" + url, headers={"user-agent": "EVEREST-evidence (github.com/Yizebaba/EVEREST-)"})
    import socket
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            final = r.geturl(); loc = r.headers.get("content-location") or ""; st = r.status
    except urllib.error.HTTPError as e:
        return {"status": e.code, "err": str(e)[:120]}
    m = re.search(r"/web/(\d{14})/", final) or re.search(r"/web/(\d{14})/", loc)
    if not m: return {"status": st, "err": "no snapshot url"}
    ts = m.group(1)
    return {"status": st, "archive": f"https://web.archive.org/web/{ts}/{url}", "t": f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}T{ts[8:10]}:{ts[10:12]}:{ts[12:14]}Z"}


def wayback_attach(pack):
    import time as _t
    db = json.load(open(WAYBACK_DB)) if os.path.exists(WAYBACK_DB) else {}
    n_new = 0
    for it in pack.get("timeline", []):
        u = it.get("url") or ""
        if it.get("kind") not in ("SUPPORTING", "CONTRADICTORY") or not u.startswith("http") or "web.archive.org" in u or "github.com/Yizebaba" in u: continue
        rec = db.get(u)
        if (not rec or not rec.get("archive")) and WAYBACK_BUDGET[0] > 0 and time.time() < WAYBACK_DEADLINE[0] and not (rec and rec.get("tries", 0) >= 3):
            WAYBACK_BUDGET[0] -= 1
            import threading
            box = {}
            def _w():
                try: box["r"] = wayback_save(u)
                except Exception as e: box["r"] = {"err": str(e)[:120]}
            th = threading.Thread(target=_w, daemon=True); th.start(); th.join(60)   # 硬上限 60 秒，卡住就放弃这一个
            r = box.get("r") or {"err": "timeout 60s"}
            r["tries"] = (rec or {}).get("tries", 0) + 1; r["asked"] = iso(NOW); db[u] = rec = r; n_new += 1
            if r.get("status") == 429: WAYBACK_BUDGET[0] = 0   # 被限流就停，下次再存
            _t.sleep(5)
        if rec and rec.get("archive"):
            it["archive"] = rec["archive"]; it["archive_t"] = rec["t"]
    json.dump(db, open(WAYBACK_DB, "w"), ensure_ascii=False, indent=1)
    pack["archive_note"] = "带 archive 字段的条目：原始网页已由互联网档案馆时光机（Wayback Machine，独立第三方）存档，archive_t 是存档时间。存档证明那一刻网页的样子，不证明网页内容属实。"
    pack["archive_n"] = sum(1 for it in pack.get("timeline", []) if it.get("archive"))
    if n_new: print("wayback: 新存档请求", n_new, "，本条证据包已有存档", pack["archive_n"])

def main():
    os.makedirs(OUT, exist_ok=True)
    idx_p = "index.json"; idx = json.load(open(idx_p)) if os.path.exists(idx_p) else {"events": {}}
    if os.path.exists("manual.json"):
        MANUAL.update(json.load(open("manual.json")))
        try:   # 人工证据清单本身也存证：所有条目（含待核实的）指纹在这一刻已经存在
            ots_stamp("manual", "manual.json", idx.setdefault("manual", {}))
        except Exception as e:
            print("人工证据存证失败：", e)
    try:
        evs = get("https://everest-facets.yizebaba.workers.dev/api/events.json").get("events", [])
    except Exception as e:   # Worker 暂时不可用时，用上次保存的事件原始记录重算
        print("Worker 不可用，用上次的事件记录：", e)
        evs = [json.load(open(os.path.join(OUT, k + ".event.json"))) for k in idx["events"] if os.path.exists(os.path.join(OUT, k + ".event.json"))]
        if not evs:
            evs = []
            for k, m in idx["events"].items():
                p = json.load(open(os.path.join(OUT, k + ".json")))
                src = [x for x in p["timeline"] if x["src"] in ("BIPAD 灾害警报", "GDACS", "BIPAD 水位站", "新闻（GDELT）") or (x["src"] == "USGS 地震目录" and "崩塌" in x["text"])]
                evs.append({"id": k, "title": p["title"], "title_en": p.get("title_en"), "kind": p.get("kind"), "place": p.get("place"), "lat": p["lat"], "lon": p["lon"],
                            "t": p["t"], "first_seen": m.get("first_seen"), "src": src[:m.get("src_n", len(src))]})
    try:   # 灾种扫描发现的事件候选：和已有事件 36 小时 / 150 km 内重复的不另做
        for c in json.load(open("hazards/scan_events.json")).get("events", []):
            if not any(abs((P(c["t"]) - P(e["t"])).total_seconds()) < 36 * 3600 and km((c["lat"], c["lon"]), (e["lat"], e["lon"])) < 150 for e in evs):
                evs.append(c)
    except Exception as e:
        print("没有灾种扫描候选：", e)
    for ev in evs:
        age = (NOW - P(ev["t"])).days
        old = idx["events"].get(ev["id"])
        fresh = old and old.get("v") == VERSION and old.get("src_n") == len(ev.get("src", [])) and old.get("man") == manual_sig(ev["id"]) and (age > 14 or (NOW - P(old["built"])).total_seconds() < 50 * 60)
        if fresh:
            continue
        print("build", ev["id"]); RECEIPTS.clear(); pack = build(ev)
        pack["receipts"] = list({r["url"] + r["sha256"]: r for r in RECEIPTS}.values())
        pack["receipts_note"] = "取数回执：生成这份证据包时向各来源发出的请求、时间和返回内容的 SHA-256；小的文本响应原样存在 events/raw/。回执随证据包一起存证。"
        json.dump(pack, open(os.path.join(OUT, ev["id"] + ".json"), "w"), ensure_ascii=False, indent=1)
        json.dump(ev, open(os.path.join(OUT, ev["id"] + ".event.json"), "w"), ensure_ascii=False, indent=1)
        ots_prev = (idx["events"].get(ev["id"]) or {}).get("ots", [])
        idx["events"][ev["id"]] = {"ots": ots_prev, "title": ev["title"], "t": pack["t"], "t_detected": ev["t"], "t_prec": pack.get("t_prec"), "first_seen": ev.get("first_seen"), "kind": ev.get("kind"), "place": ev.get("place"), "lat": ev["lat"], "lon": ev["lon"],
                                   "v": VERSION, "man": manual_sig(ev["id"]), "n": len(pack["timeline"]), "src_n": len(ev.get("src", [])), "built": pack["built"],
                                   "missing": sum(1 for i in pack["timeline"] if i["kind"] == "MISSING")}
        try:
            prov_export(pack)
        except Exception as e:
            print("PROV 导出失败：", e)
        try:
            ots_stamp(ev["id"], os.path.join(OUT, ev["id"] + ".json"), idx["events"][ev["id"]])
        except Exception as e:
            print("OpenTimestamps 失败：", e)
        try:
            rocrate_export(pack, idx["events"][ev["id"]])
        except Exception as e:
            print("RO-Crate 导出失败：", e)
    live = {e["id"] for e in evs}
    for k in list(idx["events"]):
        if k not in live:   # 已并入别的事件或超过 60 天
            idx["events"].pop(k)
            for f in (k + ".json", k + "_evn.png", k + ".event.json"):
                if os.path.exists(os.path.join(OUT, f)): os.remove(os.path.join(OUT, f))
    try:
        ots_upgrade(idx)
    except Exception as e:
        print("OpenTimestamps 升级失败：", e)
    idx["updated"] = iso(NOW)
    json.dump(idx, open(idx_p, "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
