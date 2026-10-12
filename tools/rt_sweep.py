#!/usr/bin/env python3
"""接入前核对：GIBS 图像/时间域、EUMETView IODC 图层、IGN HTTPS 上的 DORIS NRT。"""
import json, re, sys, urllib.request, datetime as dt
NOW = dt.datetime.now(dt.timezone.utc); out = {"t": NOW.isoformat(timespec="seconds"), "r": {}}
def get(u, t=60):
    with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "everest-check"}), timeout=t) as r:
        return r.status, r.headers.get("content-type"), r.read()
def run(k, u, keep=600):
    try:
        st, ct, b = get(u); out["r"][k] = {"status": st, "ct": ct, "bytes": len(b), "head": b[:keep].decode("latin1") if not (ct or "").startswith("image") else None}
    except Exception as e: out["r"][k] = {"err": repr(e)[:200]}
    print(k, json.dumps(out["r"][k])[:700], flush=True)
B = "BBOX=27.3,86.2,28.7,87.7&WIDTH=450&HEIGHT=420"
run("gibs_wms_vis_default", f"https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi?SERVICE=WMS&REQUEST=GetMap&VERSION=1.3.0&LAYERS=Himawari_AHI_Band3_Red_Visible_1km&CRS=EPSG:4326&{B}&FORMAT=image/png&STYLES=")
run("gibs_wms_ir_default", f"https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi?SERVICE=WMS&REQUEST=GetMap&VERSION=1.3.0&LAYERS=Himawari_AHI_Band13_Clean_Infrared&CRS=EPSG:4326&{B}&FORMAT=image/png&STYLES=")
d = NOW.strftime("%Y-%m-%d")
for tms in ("1km", "2km", "500m"):
    run(f"gibs_domains_{tms}", f"https://gibs.earthdata.nasa.gov/wmts/epsg4326/best/1.0.0/Himawari_AHI_Band3_Red_Visible_1km/default/{tms}/all/{d}T00:00:00Z--{d}T23:59:59Z.xml", 1500)
run("gibs_domains_ir_2km", f"https://gibs.earthdata.nasa.gov/wmts/epsg4326/best/1.0.0/Himawari_AHI_Band13_Clean_Infrared/default/2km/all/{d}T00:00:00Z--{d}T23:59:59Z.xml", 1500)
st, ct, cap = get("https://view.eumetsat.int/geoserver/ows?service=WMS&version=1.3.0&request=GetCapabilities", 120)
txt = cap.decode("utf-8", "replace")
lay = re.findall(r"<Layer[^>]*>\s*<Name>(msg_iodc:[^<]+)</Name>\s*<Title>([^<]*)</Title>", txt)
out["r"]["eumet_iodc_layers"] = lay
for name in ("msg_iodc:rgb_naturalenhncd", "msg_iodc:rgb_natural", "msg_iodc:vis006", "msg_iodc:ir108"):
    if any(n == name for n, _ in lay):
        run("eumet_getmap_" + name, f"https://view.eumetsat.int/geoserver/ows?service=WMS&version=1.3.0&request=GetMap&layers={name}&styles=&crs=EPSG:4326&{B}&format=image/png")
for u in ("https://doris.ign.fr/pub/doris/data/srl/NRT/", "http://doris.ign.fr/pub/doris/data/srl/NRT/"):
    run("ign_https_" + u.split(":")[0], u, 1200)
json.dump(out, open(sys.argv[1], "w"), indent=1)
