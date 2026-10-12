#!/usr/bin/env python3
"""一次性排查第 3 步：IODA 萨加玛塔区（3027，含珠峰所在的索卢昆布）网络连通性是否有实时信号。"""
import json, sys, urllib.request, datetime as dt
NOW = dt.datetime.now(dt.timezone.utc); frm = int((NOW - dt.timedelta(hours=12)).timestamp()); until = int(NOW.timestamp())
u = f"https://api.ioda.inetintel.cc.gatech.edu/v2/signals/raw/region/3027?from={frm}&until={until}"
d = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "everest-sweep"}), timeout=60).read()).get("data", [])
flat = d[0] if d and isinstance(d[0], list) else d
out = {"t": NOW.isoformat(timespec="seconds"), "now_epoch": until, "signals": [
    {"src": s.get("datasource"), "from": s.get("from"), "until": s.get("until"), "step": s.get("step"),
     "last": [v for v in (s.get("values") or []) if v is not None][-3:], "n_nonnull": sum(1 for v in (s.get("values") or []) if v is not None)} for s in flat]}
json.dump(out, open(sys.argv[1], "w"), indent=1); print(json.dumps(out)[:2000])
