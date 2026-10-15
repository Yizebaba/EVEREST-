"""哥白尼数据空间目录：珠峰上空最新的哨兵一号 / 二号 / 三号过境，以及 InSAR 用的 23790 条带（与 tools/live_collect.py 同一查询）。
随灾种扫描每小时跑（GitHub 运行器能访问 CDSE），写 <out>/sat.json，hub_sync 再送进总览页。只读公开目录，不下载影像。"""
import datetime as dt, json, os, sys, urllib.parse, urllib.request
OUT = sys.argv[1] if len(sys.argv) > 1 else "."
NOW = dt.datetime.now(dt.timezone.utc)
iso = lambda d: d.strftime("%Y-%m-%dT%H:%M:%SZ")
PT = "POINT(86.925 27.988)"
def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"user-agent": "everest-sat-catalog (github.com/Yizebaba/EVEREST-)"}), timeout=60) as r:
        return json.loads(r.read())
sat = {}
for coll, extra in (("SENTINEL-1", ""), ("SENTINEL-2", " and contains(Name,'L1C')"), ("SENTINEL-3", " and contains(Name,'OL_1_EFR')")):
    f = (f"Collection/Name eq '{coll}' and OData.CSC.Intersects(area=geography'SRID=4326;{PT}')"
         f" and ContentDate/Start gt {(NOW - dt.timedelta(days=20)).strftime('%Y-%m-%dT%H:%M:%S.000Z')}{extra}")
    v = get("https://catalogue.dataspace.copernicus.eu/odata/v1/Products?" + urllib.parse.urlencode({"$filter": f, "$orderby": "ContentDate/Start desc", "$top": "6"})).get("value", [])
    sat[coll] = [{"name": x["Name"], "start": x["ContentDate"]["Start"], "pub": x.get("PublicationDate"), "online": x.get("Online")} for x in v]
f = ("BurstId eq 23790 and SwathIdentifier eq 'IW1' and PolarisationChannels eq 'VV'"
     f" and ContentDate/Start gt {(NOW - dt.timedelta(days=40)).strftime('%Y-%m-%dT%H:%M:%S.000Z')}")
v = get("https://catalogue.dataspace.copernicus.eu/odata/v1/Bursts?" + urllib.parse.urlencode({"$filter": f, "$orderby": "ContentDate/Start desc", "$top": "6"})).get("value", [])
sat["BURST_23790"] = [{"name": x.get("ParentProductName") or x.get("Name"), "start": x["ContentDate"]["Start"], "platform": x.get("PlatformSerialIdentifier"),
                       "orbit": x.get("RelativeOrbitNumber"), "dir": x.get("OrbitDirection")} for x in v]
json.dump({"fetched": iso(NOW), "sat": sat}, open(os.path.join(OUT, "sat.json"), "w"), ensure_ascii=False)
print({k: (x[0]["start"] if x else None) for k, x in sat.items()})
