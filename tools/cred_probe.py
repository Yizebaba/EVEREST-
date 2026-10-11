#!/usr/bin/env python3
"""检查完整流程需要的授权是否已配置、能不能用。只输出“有/没有/成功/失败”，绝不输出任何密钥内容。"""
import json, os, sys, datetime as dt, urllib.request, urllib.parse
out = {"t": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "secrets": {}, "checks": {}}
for k in ("OPENEO_REFRESH_TOKEN", "CDSE_USERNAME", "CDSE_PASSWORD", "GH_PAT"):
    out["secrets"][k] = bool(os.environ.get(k))
def clean(e):
    s = repr(e)
    for k in ("OPENEO_REFRESH_TOKEN", "CDSE_USERNAME", "CDSE_PASSWORD", "GH_PAT"):
        v = os.environ.get(k)
        if v: s = s.replace(v, "***")
    return s[:240]
import openeo
URL = "https://openeo.dataspace.copernicus.eu"
# 1 refresh token（仓库工作流用的方式）
if os.environ.get("OPENEO_REFRESH_TOKEN"):
    try:
        raw = os.environ["OPENEO_REFRESH_TOKEN"]
        p = os.path.expanduser("~/.local/share/openeo-python-client"); os.makedirs(p, exist_ok=True)
        try: parsed = json.loads(raw)
        except json.JSONDecodeError: parsed = raw
        open(p + "/refresh-tokens.json", "w").write(json.dumps(parsed) if not isinstance(parsed, str) else parsed)
        c = openeo.connect(URL); c.authenticate_oidc_refresh_token()
        jobs = c.list_jobs()
        out["checks"]["openeo_refresh"] = {"ok": True, "jobs": len(jobs), "titles": [j.get("title") for j in jobs][:10]}
    except Exception as e:
        out["checks"]["openeo_refresh"] = {"ok": False, "err": clean(e)}
# 2 账号密码换令牌（备用方式）
if os.environ.get("CDSE_USERNAME") and os.environ.get("CDSE_PASSWORD"):
    try:
        data = urllib.parse.urlencode({"client_id": "cdse-public", "grant_type": "password",
                                       "username": os.environ["CDSE_USERNAME"], "password": os.environ["CDSE_PASSWORD"]}).encode()
        r = json.loads(urllib.request.urlopen(urllib.request.Request(
            "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token", data=data), timeout=60).read())
        out["checks"]["cdse_password_grant"] = {"ok": "access_token" in r, "has_refresh": "refresh_token" in r}
        try:
            c = openeo.connect(URL); c.authenticate_oidc_access_token(r["access_token"], provider_id="CDSE")
            out["checks"]["openeo_with_password_token"] = {"ok": True, "jobs": len(c.list_jobs())}
        except Exception as e:
            out["checks"]["openeo_with_password_token"] = {"ok": False, "err": clean(e)}
    except Exception as e:
        out["checks"]["cdse_password_grant"] = {"ok": False, "err": clean(e)}
# 3 openEO 公开能力（无需登录）：确认仓库要调用的干涉算法可用
try:
    c = openeo.connect(URL)
    ns = "https://raw.githubusercontent.com/ESA-APEx/apex_algorithms/refs/heads/main/algorithm_catalog/eurac/sentinel1_sar_interferogram/openeo_udp/sentinel1_sar_interferogram.json"
    udp = json.loads(urllib.request.urlopen(ns, timeout=60).read())
    out["checks"]["udp"] = {"ok": True, "id": udp.get("id"), "params": [p["name"] for p in udp.get("parameters", [])]}
    out["checks"]["openeo_public"] = {"ok": True, "api": c.capabilities().api_version(), "providers": [p.get("id") for p in c.get("/credentials/oidc").json().get("providers", [])]}
except Exception as e:
    out["checks"]["openeo_public"] = {"ok": False, "err": clean(e)}
json.dump(out, open(sys.argv[1], "w"), ensure_ascii=False, indent=1)
print(json.dumps({"secrets": out["secrets"], "checks": {k: v.get("ok") for k, v in out["checks"].items()}}))
