"""事件证据包：把公开来源对齐到同一条时间线。在 GitHub 运行器上跑（events 分支的 evidence 工作流），只做小量取数和画图。

输入：Worker 自动发现的事件（https://everest-facets.yizebaba.workers.dev/api/events.json）
输出：events/<事件编号>.json（时间线）、events/<事件编号>_evn.png（IO.EVN 信号图）、index.json（目录）

每个证据包包含：
  - 事件本身的公开信号（BIPAD 警报、USGS、GDACS、水位越线）
  - IO.EVN 地震台（珠峰 Pyramid，GEOFON）事件前 24 小时到后 3 小时的 1–5 Hz 信号包络，标出最强的几段
  - USGS、EMSC 在事件 300 km 内、前后一天的目录记录
  - 事件 80 km 内 BIPAD 水位站的当前状态（是否在报、是否越线）
  - 所在区的 IODA 网络连通（BGP、主动探测）前后变化
  - 哥白尼应急制图（Copernicus EMS）是否启动
  - Sentinel-1 / Sentinel-2 在事件前最近一景、事件后第一景（微软 Planetary Computer 目录，附预览链接）
只陈述公开来源记录了什么、什么时候；不判断成因，不预测。
"""
import json, math, os, re, sys, time, traceback
from datetime import datetime, timedelta, timezone
import urllib.request, urllib.parse

UA = {"user-agent": "everest-evidence (github.com/Yizebaba/everest-insar-pipeline)"}
EVN = (27.9587, 86.8117)
OUT = "events"
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
                items.append({"t": iso(p[0]), "src": "IO.EVN 地震台", "kind": "SUPPORTING", "text": f"1–5 Hz 信号约为背景的 {p[1]:.0f} 倍（台站距事件约 {dist} km；只说明此时有强信号，来源未判定）"})
        else:
            items.append({"t": iso(t0), "src": "IO.EVN 地震台", "kind": "NEUTRAL", "text": f"事件前 24 小时到后 3 小时没有超过背景 5 倍的信号（距约 {dist} km，数据覆盖 {cover}%）"})
        if cover < 80:
            items.append({"t": iso(a), "src": "IO.EVN 地震台", "kind": "MISSING", "text": f"窗口内数据只覆盖 {cover}%"})
        # 画图
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        ts = [start + timedelta(minutes=i) for i in range(m)]
        fig, ax = plt.subplots(figsize=(9, 2.6), dpi=110)
        ax.plot(ts, env / (bg or 1), lw=0.7, color="#d9822b"); ax.set_yscale("log"); ax.axhline(1, color="#999", lw=0.5)
        ax.axvline(t0, color="#3b82f6", lw=1, ls="--"); ax.set_ylabel("× 背景" if False else "x background")
        ax.set_title(f"IO.EVN BHZ 1-5 Hz, 60 s RMS  |  {ev['id']}  |  dashed = first public signal", fontsize=8)
        fig.autofmt_xdate(); fig.tight_layout(); fig.savefig(os.path.join(OUT, f"{ev['id']}_evn.png")); plt.close(fig)
    except Exception as e:
        pack["evn"] = {"distance_km": dist, "error": str(e)[:200]}
        items.append({"t": iso(t0), "src": "IO.EVN 地震台", "kind": "MISSING", "text": f"取不到这段波形（{str(e)[:80]}）"})


def catalogs(ev, t0, items):
    a, b = t0 - timedelta(days=1), t0 + timedelta(days=1)
    try:
        x = get(f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&latitude={ev['lat']}&longitude={ev['lon']}&maxradiuskm=300&starttime={iso(a)}&endtime={iso(b)}")
        for f in x.get("features", []):
            p = f["properties"]
            items.append({"t": iso(datetime.fromtimestamp(p["time"] / 1000, timezone.utc)), "src": "USGS 地震目录", "kind": "SUPPORTING",
                          "text": f"M{p['mag']} {'崩塌/滑坡（非构造）' if p.get('type') == 'landslide' else p.get('type')} · {p.get('place')}", "url": p.get("url")})
        if not x.get("features"):
            items.append({"t": iso(t0), "src": "USGS 地震目录", "kind": "NEUTRAL", "text": "事件 300 km 内前后一天没有记录"})
    except Exception as e:
        items.append({"t": iso(t0), "src": "USGS 地震目录", "kind": "MISSING", "text": f"查询失败（{str(e)[:60]}）"})
    try:
        x = get(f"https://www.seismicportal.eu/fdsnws/event/1/query?format=json&lat={ev['lat']}&lon={ev['lon']}&maxradius=2.7&start={iso(a)[:-1]}&end={iso(b)[:-1]}")
        fs = x.get("features", [])
        for f in fs:
            p = f["properties"]
            items.append({"t": p["time"][:19] + "Z", "src": "EMSC 地震目录", "kind": "SUPPORTING", "text": f"{p.get('magtype')} {p.get('mag')} · {p.get('flynn_region')}"})
        if not fs:
            items.append({"t": iso(t0), "src": "EMSC 地震目录", "kind": "NEUTRAL", "text": "事件 300 km 内前后一天没有记录"})
    except Exception as e:
        items.append({"t": iso(t0), "src": "EMSC 地震目录", "kind": "NEUTRAL", "text": "事件 300 km 内前后一天没有记录" if "204" in str(e) else f"查询失败（{str(e)[:60]}）"})


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
                      "text": f"事件 80 km 内 {len(out)} 个公开水位站，现在在报 {nrep} 个" + ("；停报：" + "、".join(g["title"] for g in out if not g["reporting"]) if nrep < len(out) else "")})
    except Exception as e:
        items.append({"t": iso(NOW), "src": "BIPAD 水位站", "kind": "MISSING", "text": f"查询失败（{str(e)[:60]}）"})


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
                              "text": f"{z} 区 {s['datasource']} 从 {base:.0f} 降到 {low:.0f}"})
        pack["ioda"] = res
        if not any(i["src"] == "IODA 网络连通" for i in items):
            items.append({"t": iso(t0), "src": "IODA 网络连通", "kind": "NEUTRAL", "text": f"{z} 区事件前后 24 小时没有明显下降"})
    except Exception as e:
        items.append({"t": iso(t0), "src": "IODA 网络连通", "kind": "MISSING", "text": f"查询失败（{str(e)[:60]}）"})


def ems(ev, t0, items):
    try:
        x = get("https://emergency.copernicus.eu/mapping/activations-rapid/feed", raw=True).decode("utf8", "ignore")
        hits = []
        for it in re.findall(r"<item>(.*?)</item>", x, re.S):
            title = re.search(r"<title>(.*?)</title>", it, re.S); link = re.search(r"<link>(.*?)</link>", it, re.S); pd = re.search(r"<pubDate>(.*?)</pubDate>", it, re.S)
            if title and "Nepal" in title.group(1):
                try:
                    t = datetime.strptime(pd.group(1).strip()[:25], "%a, %d %b %Y %H:%M:%S").replace(tzinfo=timezone.utc)
                except Exception:
                    t = None
                if t and t0 - timedelta(days=2) <= t <= t0 + timedelta(days=14):
                    hits.append((t, title.group(1).strip(), link.group(1).strip() if link else None))
        for t, ti, ln in hits:
            items.append({"t": iso(t), "src": "Copernicus EMS", "kind": "SUPPORTING", "text": "启动应急制图：" + ti, "url": ln})
        if not hits:
            items.append({"t": iso(NOW), "src": "Copernicus EMS", "kind": "NEUTRAL", "text": "没有找到涉及这次事件的应急制图启动"})
    except Exception as e:
        items.append({"t": iso(NOW), "src": "Copernicus EMS", "kind": "MISSING", "text": f"查询失败（{str(e)[:60]}）"})


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
                items.append({"t": before["t"], "src": name, "kind": "NEUTRAL", "text": f"事件前最近一景 {before['id']}" + (f"（云量 {before['cloud']:.0f}%）" if before.get("cloud") is not None else ""), "url": before.get("preview")})
            if after:
                items.append({"t": after["t"], "src": name, "kind": "SUPPORTING", "text": f"事件后第一景 {after['id']}" + (f"（云量 {after['cloud']:.0f}%）" if after.get("cloud") is not None else "") + "，可与事件前对比", "url": after.get("preview")})
            else:
                items.append({"t": iso(NOW), "src": name, "kind": "MISSING", "text": "事件后还没有新的一景（下次自动补）"})
        except Exception as e:
            items.append({"t": iso(NOW), "src": name, "kind": "MISSING", "text": f"目录查询失败（{str(e)[:60]}）"})
    pack["sentinel"] = res


def build(ev):
    t0 = P(ev["t"]); items = []
    m = re.search(r"bipad-([a-z-]+)-\d{4}", ev["id"])
    if m:
        ev["district"] = next((d for d in DIST if d.lower() == m.group(1).replace("-", " ") or d.lower() == m.group(1)), None)
    for s in ev.get("src", []):
        items.append({"t": s["t"], "src": s["src"], "kind": "SUPPORTING", "text": s["text"], "url": s.get("url")})
    pack = {"id": ev["id"], "title": ev["title"], "kind": ev.get("kind"), "place": ev.get("place"), "lat": ev["lat"], "lon": ev["lon"], "t": ev["t"]}
    for fn in (lambda: evn(ev, t0, items, pack), lambda: catalogs(ev, t0, items), lambda: gauges(ev, t0, items, pack),
               lambda: ioda(ev, t0, items, pack), lambda: ems(ev, t0, items), lambda: sentinel(ev, t0, items, pack)):
        try:
            fn()
        except Exception:
            traceback.print_exc()
    items.sort(key=lambda i: i["t"])
    pack["timeline"] = items; pack["built"] = iso(NOW)
    pack["note"] = "只陈述公开来源记录了什么、什么时候；不判断成因，不预测。地震台强信号只说明那一刻台站记录到较强震动，来源需要结合其他证据。"
    return pack


def main():
    os.makedirs(OUT, exist_ok=True)
    evs = get("https://everest-facets.yizebaba.workers.dev/api/events.json").get("events", [])
    idx_p = "index.json"; idx = json.load(open(idx_p)) if os.path.exists(idx_p) else {"events": {}}
    for ev in evs:
        age = (NOW - P(ev["t"])).days
        old = idx["events"].get(ev["id"])
        fresh = old and old.get("src_n") == len(ev.get("src", [])) and (age > 14 or (NOW - P(old["built"])).total_seconds() < 5 * 3600)
        if fresh:
            continue
        print("build", ev["id"]); pack = build(ev)
        json.dump(pack, open(os.path.join(OUT, ev["id"] + ".json"), "w"), ensure_ascii=False, indent=1)
        idx["events"][ev["id"]] = {"title": ev["title"], "t": ev["t"], "first_seen": ev.get("first_seen"), "kind": ev.get("kind"), "place": ev.get("place"), "lat": ev["lat"], "lon": ev["lon"],
                                   "n": len(pack["timeline"]), "src_n": len(ev.get("src", [])), "built": pack["built"],
                                   "missing": sum(1 for i in pack["timeline"] if i["kind"] == "MISSING")}
    idx["updated"] = iso(NOW)
    json.dump(idx, open(idx_p, "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
