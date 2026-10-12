#!/usr/bin/env python3
"""一次性大排查第 2 步：卢卡拉两台 Raspberry Shake 的实时性；中国地震台网速报；IODA 尼泊尔。"""
import json, re, sys, time, ssl, urllib.request, datetime as dt
NOW = dt.datetime.now(dt.timezone.utc); out = {"t": NOW.isoformat(timespec="seconds"), "r": {}}
def get(u, hdr=None, insecure=False, t=60):
    h = {"User-Agent": "Mozilla/5.0 everest-sweep"}; h.update(hdr or {})
    ctx = ssl._create_unverified_context() if insecure else None
    with urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=t, context=ctx) as r: return r.read().decode("utf-8", "replace")
def run(name, fn):
    try: out["r"][name] = {"ok": True, **fn()}
    except Exception as e: out["r"][name] = {"ok": False, "err": repr(e)[:300]}
    print(name, json.dumps(out["r"][name], ensure_ascii=False)[:800], flush=True)
def rs():
    from obspy.clients.fdsn import Client; from obspy import UTCDateTime
    c = Client("RASPISHAKE"); now = UTCDateTime(); res = {}
    for sta in ("R5A68", "RDD5D"):
        r = {}
        try:
            inv = c.get_stations(network="AM", station=sta, level="channel")
            r["channels"] = sorted({(ch.code, str(ch.start_date)[:10], str(ch.end_date)[:10] if ch.end_date else None) for n in inv for s in n for ch in s})
        except Exception as e: r["inv_err"] = repr(e)[:80]
        for win, lab in ((1800, "last_30min"), (86400 * 3, "last_3d"), (86400 * 30, "last_30d")):
            try:
                st = c.get_waveforms("AM", sta, "*", "EHZ,SHZ,HHZ", now - win, now if win == 1800 else now - win + 3600)
                r[lab] = str(max(tr.stats.endtime for tr in st))
            except Exception as e: r[lab] = repr(e)[:50]
        res[sta] = r
    # 用 availability 查最近数据（若支持）
    try:
        txt = get("https://data.raspberryshake.org/fdsnws/availability/1/extent?network=AM&station=R5A68,RDD5D&format=text")
        res["extent"] = txt.splitlines()[:6]
    except Exception as e: res["extent"] = repr(e)[:80]
    return res
run("raspberryshake_lukla", rs)
def cenc():
    j = json.loads(get("https://news.ceic.ac.cn/ajax/google?rand=1", hdr={"Referer": "https://news.ceic.ac.cn/"}, insecure=True))
    near = [e for e in j if abs(float(e.get("EPI_LAT", 0)) - 28.0) < 3 and abs(float(e.get("EPI_LON", 0)) - 86.9) < 4]
    return {"n_all": len(j), "newest_all": [(e.get("O_TIME"), e.get("M"), e.get("LOCATION_C")) for e in j[:3]], "near": [(e.get("O_TIME"), e.get("M"), e.get("LOCATION_C"), e.get("EPI_LAT"), e.get("EPI_LON")) for e in near[:10]], "note": "证书已过期，只能跳过校验访问"}
run("china_cenc_catalog", cenc)
def ioda():
    ents = json.loads(get("https://api.ioda.inetintel.cc.gatech.edu/v2/entities/query?entityType=region&relatedTo=country/NP")).get("data", [])
    res = {"regions": [(e.get("code"), e.get("name")) for e in ents][:12]}
    frm = int((NOW - dt.timedelta(hours=6)).timestamp()); until = int(NOW.timestamp())
    d = json.loads(get(f"https://api.ioda.inetintel.cc.gatech.edu/v2/signals/raw/country/NP?from={frm}&until={until}")).get("data", [])
    flat = d[0] if d and isinstance(d[0], list) else d
    res["country_signals"] = [(s.get("datasource"), s.get("until"), (s.get("values") or [None])[-1]) for s in flat][:6]
    return res
run("ioda_nepal", ioda)
def nsc():
    for u in ("https://seismonepal.gov.np/", "http://seismonepal.gov.np/earthquakes", "https://www.seismonepal.gov.np/earthquakes"):
        try:
            txt = get(u, insecure=True)
            rows = re.findall(r"<tr[^>]*>(.*?)</tr>", txt, re.S)[1:5]
            return {"url": u, "rows": [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", r)).strip()[:160] for r in rows], "len": len(txt)}
        except Exception as e: last = repr(e)[:100]
    raise RuntimeError(last)
run("nepal_nsc", nsc)
json.dump(out, open(sys.argv[1], "w"), indent=1, ensure_ascii=False)
