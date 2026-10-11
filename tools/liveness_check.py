#!/usr/bin/env python3
"""实时性检测：对每个候选入口取最新数据，记录最后一条数据的时间和现在相差多久。只读。"""
import json, datetime as dt, urllib.request, traceback
NOW = dt.datetime.now(dt.timezone.utc)
out = {"checked_utc": NOW.isoformat(timespec="seconds"), "sources": []}

def get(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": "everest-liveness/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read()

def rec(name, url, latest=None, extra=None, err=None):
    d = {"name": name, "url": url}
    if latest:
        d["latest_utc"] = latest.astimezone(dt.timezone.utc).isoformat(timespec="seconds")
        d["age_minutes"] = round((NOW - latest).total_seconds() / 60, 1)
    if extra: d.update(extra)
    if err: d["error"] = err
    out["sources"].append(d); print(json.dumps(d, ensure_ascii=False))

# 1 IO.EVN 地震波形（GEOFON），以及卢卡拉两台 Raspberry Shake
try:
    from obspy.clients.fdsn import Client
    from obspy import UTCDateTime
    for label, base, net, sta, ch in [("IO.EVN 金字塔地震台", "GEOFON", "IO", "EVN", "HHZ"),
                                      ("AM.R5A68 卢卡拉公民地震仪", "RASPISHAKE", "AM", "R5A68", "EHZ"),
                                      ("AM.RDD5D 卢卡拉公民地震仪", "RASPISHAKE", "AM", "RDD5D", "EHZ")]:
        try:
            c = Client(base)
            t1 = UTCDateTime(NOW); t0 = t1 - 6 * 3600
            st = c.get_waveforms(net, sta, "*", ch, t0, t1)
            end = max(tr.stats.endtime for tr in st).datetime.replace(tzinfo=dt.timezone.utc)
            rec(label, f"{base} FDSN {net}.{sta}.{ch}", end, {"traces": len(st), "samples": int(sum(tr.stats.npts for tr in st))})
        except Exception as e:
            rec(label, f"{base} FDSN {net}.{sta}.{ch}", err=repr(e)[:300])
except Exception as e:
    rec("obspy", "-", err=repr(e)[:300])

# 2 BIPAD 水位
try:
    best = None; imja = []
    for off in (0, 100, 200, 300):
        s, b = get(f"https://bipadportal.gov.np/api/v1/river-stations/?format=json&limit=100&offset={off}")
        rows = json.loads(b).get("results", [])
        if not rows: break
        for r in rows:
            t = r.get("waterLevelOn")
            if t:
                tt = dt.datetime.fromisoformat(t)
                best = tt if best is None or tt > best else best
                if "Imja" in (r.get("title") or "") or "Rolpa" in (r.get("title") or "") or "Rolpa" in (r.get("description") or ""):
                    imja.append({"title": r.get("title"), "waterLevel": r.get("waterLevel"), "waterLevelOn": t})
    rec("BIPAD 河流水位（全国最新一条）", "https://bipadportal.gov.np/api/v1/river-stations/", best, {"imja_tsho_rolpa": imja})
except Exception as e:
    rec("BIPAD 河流水位", "https://bipadportal.gov.np/api/v1/river-stations/", err=repr(e)[:300])

# 3 BIPAD 警报
try:
    s, b = get("https://bipadportal.gov.np/api/v1/alert/?format=json&ordering=-started_on&limit=3")
    rows = json.loads(b).get("results", [])
    t = dt.datetime.fromisoformat(rows[0]["startedOn"]) if rows and rows[0].get("startedOn") else None
    rec("BIPAD 实时警报", "https://bipadportal.gov.np/api/v1/alert/", t, {"title": rows[0].get("title") if rows else None})
except Exception as e:
    rec("BIPAD 实时警报", "https://bipadportal.gov.np/api/v1/alert/", err=repr(e)[:300])

# 4 USGS 全球地震（每分钟更新的 feed）
try:
    s, b = get("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson")
    j = json.loads(b); gen = dt.datetime.fromtimestamp(j["metadata"]["generated"] / 1000, dt.timezone.utc)
    rec("USGS 实时地震 feed（生成时间）", "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson", gen, {"events_last_hour": len(j["features"])})
except Exception as e:
    rec("USGS 实时地震 feed", "-", err=repr(e)[:300])

# 5 国家地理大本营看板
try:
    s, b = get("https://datadash.appstate.edu/high-altitude-climate/lb")
    txt = b.decode("utf-8", "replace")
    import re
    stamps = sorted(set(re.findall(r"20\d\d-\d\d-\d\d \d\d:\d\d(?::\d\d)?", txt)))
    rec("国家地理珠峰站看板（页面里最新时间，尼泊尔时间）", "https://datadash.appstate.edu/high-altitude-climate/lb", None, {"latest_stamp_text_npt": stamps[-1] if stamps else None, "bytes": len(b)})
except Exception as e:
    rec("国家地理珠峰站看板", "-", err=repr(e)[:300])

# 6 意大利 EvK2 Minoprio：遥测数据页与 Pumori 直播摄像头
for label, url in [("EvK2 Minoprio 实时遥测页", "https://evk2minoprio.org/en/real-time-data-en/"),
                   ("EvK2 Minoprio Pumori 摄像头图片", "http://www.peterpyr.net/webcam.jpg")]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "everest-liveness/0.1"})
        with urllib.request.urlopen(req, timeout=60) as r:
            b = r.read(); h = dict(r.headers)
        lm = h.get("Last-Modified")
        latest = None
        if lm:
            from email.utils import parsedate_to_datetime
            latest = parsedate_to_datetime(lm)
        import re, hashlib
        txt = b.decode("utf-8", "replace") if "html" in (h.get("Content-Type") or "") else ""
        stamps = sorted(set(re.findall(r"20\d\d[-/]\d\d[-/]\d\d[ T]\d\d:\d\d", txt)))[-3:]
        rec(label, url, latest, {"status": r.status, "content_type": h.get("Content-Type"), "bytes": len(b), "sha1": hashlib.sha1(b).hexdigest()[:12], "stamps_in_page": stamps,
                                  "radar_mentioned": ("radar" in txt.lower())})
    except Exception as e:
        rec(label, url, err=repr(e)[:300])

json.dump(out, open("data/liveness/latest.json", "w"), ensure_ascii=False, indent=1)
