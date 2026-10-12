#!/usr/bin/env python3
"""一次性调查：内华达大地测量实验室（NGL）有没有珠峰附近的 GNSS 站，最新解到哪天（日解/快速/5 分钟超快速）。"""
import urllib.request, json, math, sys, re, datetime as dt
def get(u, n=None):
    r = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "everest-probe"}), timeout=120)
    return r.read(n).decode("latin1") if n else r.read().decode("latin1")
E0 = (27.988, 86.925)
def km(a, b, c, d):
    p = math.pi / 180; x = math.sin((c - a) * p / 2) ** 2 + math.cos(a * p) * math.cos(c * p) * math.sin((d - b) * p / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(x))
out = {"t": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z", "lists": {}, "near": [], "errors": []}
for name, u in [("final", "https://geodesy.unr.edu/NGLStationPages/DataHoldings.txt"),
                ("rapid", "https://geodesy.unr.edu/NGLStationPages/DataHoldingsRapid24hr.txt"),
                ("ultra", "https://geodesy.unr.edu/NGLStationPages/DataHoldingsUltra5min.txt")]:
    try:
        txt = get(u); rows = {}
        for l in txt.splitlines()[1:]:
            s = l.split()
            if len(s) < 10: continue
            try: lat, lon = float(s[1]), float(s[2])
            except ValueError: continue
            if lon > 180: lon -= 360
            d = km(E0[0], E0[1], lat, lon)
            if d < 250: rows[s[0]] = {"km": round(d), "lat": lat, "lon": lon, "h": s[3], "beg": s[7], "end": s[8], "n": s[10] if len(s) > 10 else None}
        out["lists"][name] = {"head": txt.splitlines()[0][:160], "n_lines": len(txt.splitlines()), "near": rows}
    except Exception as e:
        out["errors"].append(f"{name}: {e!r}"[:200])
# 对最近的几个站，取时间序列文件尾部
near = sorted({k: v for L in out["lists"].values() for k, v in L["near"].items()}.items(), key=lambda x: x[1]["km"])[:6]
for sta, v in near:
    for kind, u in [("tenv3", f"https://geodesy.unr.edu/gps_timeseries/IGS20/tenv3/IGS20/{sta}.tenv3"),
                    ("rapid", f"https://geodesy.unr.edu/gps_timeseries/rapids/tenv3/IGS20/{sta}.tenv3"),
                    ("ultra", f"https://geodesy.unr.edu/gps_timeseries/ultracombo/kenv/{sta}/")]:
        try:
            t = get(u)
            lines = [l for l in t.splitlines() if l.strip()]
            out["near"].append({"sta": sta, "km": v["km"], "kind": kind, "n": len(lines), "tail": lines[-2:] if kind != "ultra" else re.findall(r'href="([^"]+)"', t)[-5:]})
        except Exception as e:
            out["near"].append({"sta": sta, "kind": kind, "err": repr(e)[:120]})
json.dump(out, open(sys.argv[1], "w"), indent=1)
