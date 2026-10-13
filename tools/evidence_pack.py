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
  - 每一版证据包都存一份不可变快照，并用 OpenTimestamps 加公开时间戳（之后升级为比特币区块确认）
只陈述公开来源记录了什么、什么时候；不判断成因，不预测。
"""
import json, math, os, re, sys, time, traceback
from datetime import datetime, timedelta, timezone
import urllib.request, urllib.parse

UA = {"user-agent": "everest-evidence (github.com/Yizebaba/everest-insar-pipeline)"}
EVN = (27.9587, 86.8117)
OUT = "events"
VERSION = 6   # 改了证据包内容时加 1，所有包会重算一次
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
        valid = env[env > 0]; bg = float(np.median(valid)) if len(valid) else 0
        cover = round(100 * len(valid) / max(1, int((b - a).total_seconds() / 60)))
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
            items.append({"t": iso(p[0]), "src": "KKN 地震台", "kind": "SUPPORTING",
                          "text": f"1–5 Hz 信号约为背景的 {p[1]:.0f} 倍（台站距事件约 {dist} km）" + ("；IO.EVN 同一时刻也有强信号，两台一致" if both else "；IO.EVN 这一时刻没有强信号"),
                          "text_en": f"1–5 Hz signal about {p[1]:.0f}× background (station about {dist} km away)" + ("; IO.EVN also strong at the same time — both stations agree" if both else "; IO.EVN not strong at this time")})
        for q in evp:
            if not any(abs((q - p[0]).total_seconds()) <= 180 for p in peaks) and cover >= 80:
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
    for e in idx["events"].values():
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
               lambda: gfm(ev, t0, items, pack), lambda: montandon(ev, t0, items, pack)):
        try:
            fn()
        except Exception:
            traceback.print_exc()
    try:
        plot_seis(ev, t0, pack)
    except Exception:
        traceback.print_exc()
    pack.pop("_series_evn", None); pack.pop("_series_kkn", None)
    items.sort(key=lambda i: i["t"])
    pack["timeline"] = items; pack["built"] = iso(NOW)
    pack["note_en"] = "States only what public sources recorded and when; no attribution of cause, no prediction. A strong seismic signal only means the station recorded strong shaking at that moment."
    pack["note"] = "只陈述公开来源记录了什么、什么时候；不判断成因，不预测。地震台强信号只说明那一刻台站记录到较强震动，来源需要结合其他证据。"
    return pack


def main():
    os.makedirs(OUT, exist_ok=True)
    idx_p = "index.json"; idx = json.load(open(idx_p)) if os.path.exists(idx_p) else {"events": {}}
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
        fresh = old and old.get("v") == VERSION and old.get("src_n") == len(ev.get("src", [])) and (age > 14 or (NOW - P(old["built"])).total_seconds() < 5 * 3600)
        if fresh:
            continue
        print("build", ev["id"]); pack = build(ev)
        json.dump(pack, open(os.path.join(OUT, ev["id"] + ".json"), "w"), ensure_ascii=False, indent=1)
        json.dump(ev, open(os.path.join(OUT, ev["id"] + ".event.json"), "w"), ensure_ascii=False, indent=1)
        ots_prev = (idx["events"].get(ev["id"]) or {}).get("ots", [])
        idx["events"][ev["id"]] = {"ots": ots_prev, "title": ev["title"], "t": ev["t"], "first_seen": ev.get("first_seen"), "kind": ev.get("kind"), "place": ev.get("place"), "lat": ev["lat"], "lon": ev["lon"],
                                   "v": VERSION, "n": len(pack["timeline"]), "src_n": len(ev.get("src", [])), "built": pack["built"],
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
