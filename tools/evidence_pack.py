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
import urllib.request, urllib.parse

UA = {"user-agent": "everest-evidence (github.com/Yizebaba/everest-insar-pipeline)"}
EVN = (27.9587, 86.8117)
OUT = "events"
VERSION = 9   # 改了证据包内容时加 1，所有包会重算一次
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


def get(url, data=None, timeout=60, raw=False, headers=None):
    req = urllib.request.Request(url, data=data, headers={**UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        b = r.read()
    return b if raw else json.loads(b)


def iso(d):
    return d.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def P(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)


def km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    return 6371 * 2 * math.asin(math.sqrt(math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2))


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
    d = ev.get("district") or nearest_district(ev["lat"], ev["lon"]); z = ZONE.get(d)
    if not z:
        return
    try:
        q = get(f"https://api.ioda.inetintel.cc.gatech.edu/v2/entities/query?entityType=region&search={urllib.parse.quote(z)}")
        ents = [e for e in q.get("data", []) if (e.get("attrs") or {}).get("country_code") == "NP" or "Nepal" in json.dumps(e)]
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
            if "Nepal" not in cs and "China" not in cs or not et:
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
                   "stamped": iso(NOW), "status": "pending" if ok else "failed", "err": None if ok else (r.stderr or r.stdout)[-200:]})


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
    d = ev.get("district") or (nearest_district(ev["lat"], ev["lon"]) if km((ev["lat"], ev["lon"]), DIST[nearest_district(ev["lat"], ev["lon"])]) < 60 else None)
    return d or "Nepal"


def gdelt(ev, t0, items, pack):
    """GDELT 全球新闻：这个地方的灾害新闻最早什么时候出现、有多少家媒体报道。"""
    a, b = t0 - timedelta(days=1), min(NOW, t0 + timedelta(days=5))
    q = f'"{place_word(ev)}" {HAZ_EN}' + ("" if place_word(ev) == "Nepal" else " Nepal")
    try:
        u = "https://api.gdeltproject.org/api/v2/doc/doc?" + urllib.parse.urlencode({"query": q, "mode": "artlist", "maxrecords": 75, "format": "json", "sort": "dateasc",
                                                                                     "startdatetime": a.strftime("%Y%m%d%H%M%S"), "enddatetime": b.strftime("%Y%m%d%H%M%S")})
        time.sleep(6)   # GDELT 要求每 5 秒最多一次
        raw = get(u, raw=True, timeout=60)
        arts = json.loads(raw).get("articles", []) if raw.strip().startswith(b"{") else []
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
        fq = f"groups:npl AND metadata_created:[{iso(t0 - timedelta(days=1))} TO NOW]"
        x = get("https://data.humdata.org/api/3/action/package_search?" + urllib.parse.urlencode({"q": "flood OR landslide OR avalanche OR earthquake OR disaster", "fq": fq, "sort": "metadata_created asc", "rows": 10}))
        rs = (x.get("result") or {}).get("results", [])
        for r in rs[:5]:
            items.append({"t": r["metadata_created"][:19] + "Z", "src": "OCHA HDX", "kind": "SUPPORTING", "text": f"新数据集：{r.get('title')}（{(r.get('organization') or {}).get('title', '')}）",
                          "text_en": f"New dataset: {r.get('title')} ({(r.get('organization') or {}).get('title', '')})", "url": "https://data.humdata.org/dataset/" + r["name"]})
        if not rs:
            items.append({"t": iso(t0), "src": "OCHA HDX", "kind": "NEUTRAL", "text": "事件后没有新建的尼泊尔灾害数据集", "text_en": "No new Nepal disaster dataset after the event"})
    except Exception as e:
        items.append({"t": iso(t0), "src": "OCHA HDX", "kind": "MISSING", "text": f"查询失败（{str(e)[:60]}）", "text_en": f"Query failed ({str(e)[:60]})"})


def reliefweb(ev, t0, items, pack):
    """ReliefWeb 人道报告（需要申请 appname，放在机密 RELIEFWEB_APPNAME）。"""
    app = os.environ.get("RELIEFWEB_APPNAME")
    if not app:
        items.append({"t": iso(NOW), "src": "ReliefWeb", "kind": "MISSING", "text": "需要申请 ReliefWeb appname（未配置）", "text_en": "Needs a ReliefWeb appname (not configured)"}); return
    try:
        body = {"query": {"value": f"Nepal {place_word(ev)}"}, "filter": {"field": "date.created", "value": {"from": iso(t0 - timedelta(days=1))}}, "sort": ["date.created:asc"], "limit": 10, "fields": {"include": ["title", "url", "date.created", "source.shortname"]}}
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
            x = get(f"https://api.cloudflare.com/client/v4/radar/{path}?location=NP&dateStart={a}&dateEnd={b}&format=json&limit=20", headers=H)
            r = x.get("result", {}); L = r.get("annotations") or r.get("trafficAnomalies") or []
            for o in L:
                n += 1; t = o.get("startDate") or o.get("startDate")
                items.append({"t": (t or a)[:19] + "Z", "src": "Cloudflare Radar", "kind": "SUPPORTING", "text": f"尼泊尔{name}：{o.get('description') or o.get('outage', {}).get('outageCause') or o.get('type', '')}",
                              "text_en": f"Nepal {'outage' if 'outage' in path else 'traffic anomaly'}: {o.get('description') or o.get('outage', {}).get('outageCause') or o.get('type', '')}"})
        if not n:
            items.append({"t": iso(t0), "src": "Cloudflare Radar", "kind": "NEUTRAL", "text": "事件前后没有尼泊尔网络中断或流量异常记录", "text_en": "No Nepal outage or traffic anomaly recorded around the event"})
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
                    t1 = tt[0][1] or iso(NOW)
                    if P(t1) >= t0 - timedelta(days=30): hits.append((c.get("title") or c.get("id"), href, tt[0][0])); break
        for h in hits:
            items.append({"t": (h[2] or iso(t0))[:19] + "Z", "src": "Vantor 开放影像", "kind": "SUPPORTING", "text": f"高分辨率开放影像覆盖本地：{h[0]}", "text_en": f"Open high-resolution imagery covers this area: {h[0]}",
                          "url": "https://radiantearth.github.io/stac-browser/#/external/" + h[1].replace("https://", "")})
        if not hits:
            items.append({"t": iso(NOW), "src": "Vantor 开放影像", "kind": "NEUTRAL", "text": "这次事件没有启动开放影像", "text_en": "No open imagery released for this event"})
    except Exception as e:
        items.append({"t": iso(NOW), "src": "Vantor 开放影像", "kind": "MISSING", "text": f"查询失败（{str(e)[:60]}）", "text_en": f"Query failed ({str(e)[:60]})"})


def build(ev):
    t0 = P(ev["t"]); items = []
    m = re.search(r"bipad-([a-z-]+)-\d{4}", ev["id"])
    if m:
        ev["district"] = next((d for d in DIST if d.lower() == m.group(1).replace("-", " ") or d.lower() == m.group(1)), None)
    for s in ev.get("src", []):
        items.append({"t": s["t"], "src": s["src"], "kind": "SUPPORTING", "text_en": s.get("text_en", s["text"]), "text": s["text"], "url": s.get("url")})
    pack = {"id": ev["id"], "title": ev["title"], "title_en": ev.get("title_en") or ev["title"].replace("洪水预警", "flood warning"), "kind": ev.get("kind"), "place": ev.get("place"), "lat": ev["lat"], "lon": ev["lon"], "t": ev["t"]}
    for fn in (lambda: evn(ev, t0, items, pack), lambda: kkn(ev, t0, items, pack), lambda: catalogs(ev, t0, items), lambda: gauges(ev, t0, items, pack),
               lambda: ioda(ev, t0, items, pack), lambda: ems(ev, t0, items), lambda: sentinel(ev, t0, items, pack),
               lambda: gfm(ev, t0, items, pack), lambda: montandon(ev, t0, items, pack), lambda: manual(ev, t0, items, pack),
               lambda: rshake(ev, t0, items, pack), lambda: usgs_products(ev, t0, items, pack), lambda: gnss(ev, t0, items, pack),
               lambda: gdelt(ev, t0, items, pack), lambda: wiki(ev, t0, items, pack), lambda: hdx(ev, t0, items, pack), lambda: reliefweb(ev, t0, items, pack),
               lambda: cfradar(ev, t0, items, pack), lambda: firms(ev, t0, items, pack), lambda: blackmarble(ev, t0, items, pack),
               lambda: spaceweather(ev, t0, items, pack), lambda: vantor(ev, t0, items, pack)):
        try:
            fn()
        except Exception:
            traceback.print_exc()
    try:
        plot_seis(ev, t0, pack)
    except Exception:
        traceback.print_exc()
    pack.pop("_series_evn", None); pack.pop("_series_kkn", None); pack.pop("_evn_gaps", None)
    items.sort(key=lambda i: i["t"])
    pack["timeline"] = items; pack["built"] = iso(NOW)
    pack["note_en"] = "States only what public sources recorded and when; no attribution of cause, no prediction. A strong seismic signal only means the station recorded strong shaking at that moment."
    pack["note"] = "只陈述公开来源记录了什么、什么时候；不判断成因，不预测。地震台强信号只说明那一刻台站记录到较强震动，来源需要结合其他证据。"
    return pack


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
                src = [x for x in p["timeline"] if x["src"] in ("BIPAD 灾害警报", "GDACS", "BIPAD 水位站") or (x["src"] == "USGS 地震目录" and "崩塌" in x["text"])]
                evs.append({"id": k, "title": p["title"], "title_en": p.get("title_en"), "kind": p.get("kind"), "place": p.get("place"), "lat": p["lat"], "lon": p["lon"],
                            "t": p["t"], "first_seen": m.get("first_seen"), "src": src[:m.get("src_n", len(src))]})
    for ev in evs:
        age = (NOW - P(ev["t"])).days
        old = idx["events"].get(ev["id"])
        fresh = old and old.get("v") == VERSION and old.get("src_n") == len(ev.get("src", [])) and old.get("man") == manual_sig(ev["id"]) and (age > 14 or (NOW - P(old["built"])).total_seconds() < 5 * 3600)
        if fresh:
            continue
        print("build", ev["id"]); pack = build(ev)
        json.dump(pack, open(os.path.join(OUT, ev["id"] + ".json"), "w"), ensure_ascii=False, indent=1)
        json.dump(ev, open(os.path.join(OUT, ev["id"] + ".event.json"), "w"), ensure_ascii=False, indent=1)
        ots_prev = (idx["events"].get(ev["id"]) or {}).get("ots", [])
        idx["events"][ev["id"]] = {"ots": ots_prev, "title": ev["title"], "t": ev["t"], "first_seen": ev.get("first_seen"), "kind": ev.get("kind"), "place": ev.get("place"), "lat": ev["lat"], "lon": ev["lon"],
                                   "v": VERSION, "man": manual_sig(ev["id"]), "n": len(pack["timeline"]), "src_n": len(ev.get("src", [])), "built": pack["built"],
                                   "missing": sum(1 for i in pack["timeline"] if i["kind"] == "MISSING")}
        try:
            ots_stamp(ev["id"], os.path.join(OUT, ev["id"] + ".json"), idx["events"][ev["id"]])
        except Exception as e:
            print("OpenTimestamps 失败：", e)
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
