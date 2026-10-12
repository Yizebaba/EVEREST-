#!/usr/bin/env python3
"""一次性大排查：珠峰附近还有哪些公开、可实时接入的源。每项只记录“能不能访问、最新数据多新”。"""
import json, re, sys, time, urllib.request, datetime as dt, traceback
NOW = dt.datetime.now(dt.timezone.utc)
LAT, LON = 27.988, 86.925
out = {"t": NOW.isoformat(timespec="seconds"), "r": {}}
def get(u, n=None, data=None, hdr=None, t=60):
    h = {"User-Agent": "Mozilla/5.0 everest-sweep"}; h.update(hdr or {})
    with urllib.request.urlopen(urllib.request.Request(u, data=data, headers=h), timeout=t) as r:
        b = r.read(n) if n else r.read(); return r.status, b.decode("utf-8", "replace")
def run(name, fn):
    t0 = time.time()
    try: out["r"][name] = {"ok": True, **fn()}
    except Exception as e: out["r"][name] = {"ok": False, "err": repr(e)[:300]}
    out["r"][name]["sec"] = round(time.time() - t0, 1); print(name, json.dumps(out["r"][name], ensure_ascii=False)[:600], flush=True)

def evn_channels():
    from obspy.clients.fdsn import Client; from obspy import UTCDateTime
    c = Client("GEOFON"); inv = c.get_stations(network="IO", station="EVN", level="channel")
    chans = sorted({(ch.location_code, ch.code, ch.sample_rate, str(ch.start_date)[:10], str(ch.end_date)[:10] if ch.end_date else None) for n in inv for s in n for ch in s})
    now = UTCDateTime(); lat = {}
    for loc, code, *_ in chans:
        if code[0] not in "HBSD": continue
        try:
            st = c.get_waveforms("IO", "EVN", loc or "*", code, now - 1800, now)
            lat[f"{loc}.{code}"] = round(now - max(tr.stats.endtime for tr in st))
        except Exception as e: lat[f"{loc}.{code}"] = repr(e)[:60]
    return {"channels": chans, "lag_s": lat}
run("geofon_IO.EVN_all_channels", evn_channels)

def fdsn_near(base, label):
    def f():
        u = f"{base}/fdsnws/station/1/query?latitude={LAT}&longitude={LON}&maxradius=2.0&level=station&format=text&endafter={NOW.strftime('%Y-%m-%dT%H:%M:%S')}"
        st, txt = get(u)
        rows = [l.split("|") for l in txt.splitlines() if l and not l.startswith("#")]
        return {"n": len(rows), "stations": [(r[0], r[1], r[2], r[3], r[5][:30], r[6][:10]) for r in rows][:40]}
    return f
run("raspberryshake_within_220km", fdsn_near("https://data.raspberryshake.org", "rs"))
run("earthscope_iris_within_220km", fdsn_near("https://service.iris.edu", "iris"))
run("geofon_within_220km", fdsn_near("https://geofon.gfz.de", "gfz"))

def rs_latency():
    from obspy.clients.fdsn import Client; from obspy import UTCDateTime
    rs = out["r"].get("raspberryshake_within_220km", {}).get("stations", [])
    c = Client("RASPISHAKE"); now = UTCDateTime(); res = {}
    for net, sta, lat, lon, *_ in rs[:12]:
        try:
            st = c.get_waveforms(net, sta, "*", "EHZ,SHZ,HHZ", now - 1200, now)
            res[sta] = {"lag_s": round(now - max(tr.stats.endtime for tr in st)), "lat": lat, "lon": lon}
        except Exception as e: res[sta] = {"err": repr(e)[:80], "lat": lat, "lon": lon}
    return {"latency": res}
run("raspberryshake_latency", rs_latency)

def emsc():
    st, txt = get(f"https://www.seismicportal.eu/fdsnws/event/1/query?lat={LAT}&lon={LON}&maxradius=3&starttime={(NOW-dt.timedelta(days=60)).date()}&format=json&limit=20")
    j = json.loads(txt); fs = j.get("features", [])
    return {"n": len(fs), "newest": [(f["properties"]["time"], f["properties"]["mag"], f["properties"].get("flynn_region")) for f in fs[:5]], "realtime_ws": "wss://www.seismicportal.eu/standing_order/websocket"}
run("emsc_events_and_websocket", emsc)

def cenc():
    st, txt = get("https://news.ceic.ac.cn/ajax/google?rand=1", hdr={"Referer": "https://news.ceic.ac.cn/"})
    j = json.loads(txt)
    near = [e for e in j if abs(float(e.get("EPI_LAT", 0)) - LAT) < 3 and abs(float(e.get("EPI_LON", 0)) - LON) < 4]
    return {"n_all": len(j), "newest_all": [(e.get("O_TIME"), e.get("M"), e.get("LOCATION_C")) for e in j[:3]], "near": [(e.get("O_TIME"), e.get("M"), e.get("LOCATION_C")) for e in near[:8]]}
run("china_cenc_catalog", cenc)

def nsc():
    st, txt = get("https://seismonepal.gov.np/earthquakes")
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", txt, re.S)[1:6]
    clean = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", r)).strip()[:160] for r in rows]
    return {"status": st, "rows": clean}
run("nepal_nsc_catalog", nsc)

def gibs():
    st, txt = get("https://gibs.earthdata.nasa.gov/wmts/epsg4326/best/1.0.0/WMTSCapabilities.xml", t=120)
    res = []
    for m in re.finditer(r"<Layer>(.*?)</Layer>", txt, re.S):
        blk = m.group(1); idm = re.search(r"<ows:Identifier>([^<]+)</ows:Identifier>", blk)
        if not idm: continue
        lid = idm.group(1)
        if re.search(r"Himawari|GOES|Geostationary", lid, re.I):
            dft = re.search(r"<Default>([^<]+)</Default>", blk); res.append((lid, dft.group(1) if dft else None))
    return {"n": len(res), "layers": res[:25]}
run("nasa_gibs_geostationary", gibs)

def eumetview():
    st, txt = get("https://view.eumetsat.int/geoserver/ows?service=WMS&version=1.3.0&request=GetCapabilities", t=120)
    layers = re.findall(r"<Name>([^<]*(?:iodc|IODC)[^<]*)</Name>", txt)
    tm = re.findall(r'<Dimension name="time"[^>]*>([^<]{0,4000})</Dimension>', txt)
    lasts = [t.split(",")[-1][:40] for t in tm][:5]
    return {"iodc_layers": layers[:12], "time_dim_tail": lasts}
run("eumetsat_view_iodc", eumetview)

def adsb():
    st, txt = get("https://api.adsb.lol/v2/point/27.80/86.80/60")
    j = json.loads(txt); ac = j.get("ac", [])
    return {"now_aircraft": len(ac), "sample": [(a.get("flight"), a.get("t"), a.get("alt_baro"), a.get("lat"), a.get("lon")) for a in ac[:6]]}
run("adsb_lol_khumbu", adsb)

def ioda():
    st, txt = get("https://api.ioda.inetintel.cc.gatech.edu/v2/entities/query?entityType=region&search=Koshi")
    j = json.loads(txt); ents = j.get("data", [])[:5]
    res = {"regions": [(e.get("code"), e.get("name")) for e in ents]}
    if ents:
        code = ents[0]["code"]; frm = int((NOW - dt.timedelta(hours=6)).timestamp()); until = int(NOW.timestamp())
        st, t2 = get(f"https://api.ioda.inetintel.cc.gatech.edu/v2/signals/raw/region/{code}?from={frm}&until={until}")
        d = json.loads(t2).get("data", [[]])
        res["signals"] = [(s.get("datasource"), s.get("from"), s.get("until"), (s.get("values") or [None])[-1]) for s in (d[0] if d and isinstance(d[0], list) else d)][:6]
    return res
run("ioda_internet_koshi", ioda)

def gdacs():
    st, txt = get("https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH?country=Nepal&fromdate=" + (NOW - dt.timedelta(days=60)).strftime("%Y-%m-%d"))
    j = json.loads(txt); fs = j.get("features", [])
    return {"n": len(fs), "events": [(f["properties"].get("eventtype"), f["properties"].get("name"), f["properties"].get("fromdate"), f["properties"].get("alertlevel")) for f in fs[:8]]}
run("gdacs_nepal", gdacs)

def yt():
    st, txt = get("https://www.youtube.com/watch?v=AD4-Z-ONsIc", n=900000)
    return {"isLiveNow": "\"isLiveNow\":true" in txt, "isLive": "\"isLive\":true" in txt, "title": (re.search(r"<title>([^<]+)</title>", txt) or [None, None])[1]}
run("youtube_hotel_everest_view", yt)

json.dump(out, open(sys.argv[1], "w"), indent=1, ensure_ascii=False)
