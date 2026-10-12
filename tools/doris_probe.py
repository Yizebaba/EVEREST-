#!/usr/bin/env python3
"""一次性调查第 4 步：各分析中心周解（sinex_series）最新到哪一周，是否包含 EVEC。只读 IGN 匿名 FTP。"""
import ftplib, io, json, re, subprocess, gzip, datetime as dt, sys
out = {"t": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z", "acs": {}, "errors": []}
f = ftplib.FTP("doris.ign.fr", timeout=60); f.login()
base = "/pub/doris/products/sinex_series"
dirs = sorted(n.rsplit("/", 1)[-1] for n in f.nlst(base))
out["dirs"] = dirs
for d in dirs:
    try:
        files = sorted(n.rsplit("/", 1)[-1] for n in f.nlst(f"{base}/{d}"))
        snx = [x for x in files if re.search(r"\.snx", x)]
        info = {"n": len(snx), "last": snx[-3:]}
        if snx and re.match(r"[a-z]{3}(2[4-9])", d):
            b = io.BytesIO(); f.retrbinary(f"RETR {base}/{d}/{snx[-1]}", b.write); raw = b.getvalue()
            txt = gzip.decompress(raw).decode("latin1") if snx[-1].endswith(".gz") else subprocess.run(["uncompress", "-c"], input=raw, capture_output=True).stdout.decode("latin1")
            info["has_evec"] = "EVEC" in txt
            m = re.search(r"%=SNX.{60}", txt); info["hdr"] = m.group(0) if m else txt[:80]
        out["acs"][d] = info
    except Exception as e:
        out["errors"].append(f"{d}: {e!r}"[:160])
f.quit()
json.dump(out, open(sys.argv[1], "w"), indent=1)
