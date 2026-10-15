"""GDELT 新闻线索（与 Worker 里 news() 同一个查询）。Worker 的 Cloudflare 出口 IP 是共享的，经常被 GDELT 限流（429），
所以 GitHub 运行器每小时也取一份，写到 events 分支 hazards/gdelt.json；Worker 直连失败时读这份。只是线索，不是事件。"""
import json, os, sys, time, urllib.parse, urllib.request
OUT = sys.argv[1] if len(sys.argv) > 1 else "."
Q = '(avalanche OR landslide OR "glacial lake" OR GLOF OR flood OR "debris flow" OR rockfall OR snowstorm OR blizzard OR hailstorm OR lightning OR "cold wave" OR "forest fire" OR wildfire OR earthquake OR "dam collapse" OR cholera OR dengue OR outbreak) (Nepal OR Everest OR Himalaya OR Tibet OR Xizang) sourcelang:english'
url = "https://api.gdeltproject.org/api/v2/doc/doc?" + urllib.parse.urlencode({"query": Q, "mode": "artlist", "maxrecords": "75", "format": "json", "timespan": "3d", "sort": "datedesc"}, quote_via=lambda s, *a: urllib.parse.quote(s, safe="()\":"))
err = None
for i in range(3):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"user-agent": "everest-gdelt (github.com/Yizebaba/EVEREST-)"}), timeout=60) as r:
            tx = r.read().decode("utf-8", "ignore")
        if not tx.strip().startswith("{"): raise RuntimeError("GDELT: " + tx[:80])
        s2 = lambda d: f"{d[0:4]}-{d[4:6]}-{d[6:8]}T{d[9:11]}:{d[11:13]}:{d[13:15]}Z"
        arts = [{"t": s2(x["seendate"]), "title": str(x.get("title") or "")[:200], "url": x.get("url"), "domain": x.get("domain"), "lang": x.get("language")} for x in json.loads(tx).get("articles", [])]
        json.dump({"fetched": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "arts": arts}, open(os.path.join(OUT, "gdelt.json"), "w"), ensure_ascii=False)
        print("gdelt", len(arts)); sys.exit(0)
    except Exception as e:
        err = e; time.sleep(6)
print("gdelt failed:", err)
