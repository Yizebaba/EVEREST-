"""在 GitHub 运行器上取珠峰周边（卢卡拉附近）的 ADS-B 航空器，写 adsb.json。
Cloudflare 的服务器连不上 OpenSky，这里代为取数；由 Cloudflare 实时采集每 15 分钟触发一次。
顺序：OpenSky 注册账号（有 OPENSKY_CLIENT_ID/SECRET 时）→ OpenSky 匿名 → adsb.fi → adsb.lol。
各网站要求：OpenSky 注册每天 4000 点、匿名 400 点，本查询每次 1 点；adsb.fi / adsb.lol 公开接口限 1 次/秒。"""
import json, os, time, urllib.request, urllib.parse
UA = {"User-Agent": "everest-adsb (github.com/Yizebaba/everest-insar-pipeline)"}
BOX = "lamin=27.45&lomin=86.35&lamax=28.25&lomax=87.25"
def get(url, headers=None, data=None):
    req = urllib.request.Request(url, data=data, headers={**UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())
def opensky(tok=None):
    o = get("https://opensky-network.org/api/states/all?" + BOX, {"Authorization": "Bearer " + tok} if tok else None)
    return [{"hex": v[0], "flight": (v[1] or "").strip(), "type": None, "alt": None if v[7] is None else round(v[7] * 3.281),
             "gs": None if v[9] is None else round(v[9] * 1.944), "lat": v[6], "lon": v[5], "seen": o["time"] - (v[4] or o["time"])} for v in (o.get("states") or [])]
def readsb(url):
    x = get(url)
    return [{"hex": a.get("hex"), "flight": (a.get("flight") or "").strip(), "type": a.get("t"), "alt": a.get("alt_baro"), "gs": a.get("gs"),
             "lat": a.get("lat"), "lon": a.get("lon"), "seen": a.get("seen")} for a in (x.get("ac") or x.get("aircraft") or [])]
errs, ac, src = [], None, None
cid, sec = os.environ.get("OPENSKY_CLIENT_ID"), os.environ.get("OPENSKY_CLIENT_SECRET")
if cid and sec:
    try:
        t = get("https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token",
                {"Content-Type": "application/x-www-form-urlencoded"},
                urllib.parse.urlencode({"grant_type": "client_credentials", "client_id": cid, "client_secret": sec}).encode())
        ac, src = opensky(t["access_token"]), "opensky（注册）"
    except Exception as e: errs.append("opensky注册:" + str(e)[:60])
for name, fn in [("opensky（匿名）", lambda: opensky()), ("adsb.fi", lambda: readsb("https://opendata.adsb.fi/api/v3/lat/27.85/lon/86.80/dist/40")),
                 ("adsb.lol", lambda: readsb("https://api.adsb.lol/v2/point/27.85/86.80/40"))]:
    if ac is not None: break
    try: ac, src = fn(), name
    except Exception as e: errs.append(name + ":" + str(e)[:60])
out = {"at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "ok": ac is not None, "source": src, "count": len(ac or []), "now": ac or [], "errs": errs,
       "runner": "GitHub Actions", "box": BOX}
json.dump(out, open("adsb.json", "w"), ensure_ascii=False)
print(json.dumps({k: out[k] for k in ("at", "ok", "source", "count", "errs")}, ensure_ascii=False))
