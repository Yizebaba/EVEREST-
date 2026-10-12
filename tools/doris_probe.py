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
        def key(x):
            m = re.match(r"[a-z]{3}(\d\d)(\d{3})", x)
            if not m: return (0, 0)
            y = int(m.group(1)); return (1900 + y if y >= 90 else 2000 + y, int(m.group(2)))
        snx = sorted([x for x in files if re.search(r"\.snx(\.Z|\.gz)?$", x) and key(x) != (0, 0)], key=key)
        info = {"n": len(snx), "last": snx[-3:]}
        if snx: info["last_date"] = "%d-%03d" % key(snx[-1])
        if snx and key(snx[-1])[0] >= 2025:
            b = io.BytesIO(); f.retrbinary(f"RETR {base}/{d}/{snx[-1]}", b.write); raw = b.getvalue()
            txt = gzip.decompress(raw).decode("latin1") if snx[-1].endswith(".gz") else subprocess.run(["uncompress", "-c"], input=raw, capture_output=True).stdout.decode("latin1")
            info["has_evec"] = "EVEC" in txt
            m = re.search(r"%=SNX.{60}", txt); info["hdr"] = m.group(0) if m else txt[:80]
        out["acs"][d] = info
    except Exception as e:
        out["errors"].append(f"{d}: {e!r}"[:160])
f.quit()
json.dump(out, open(sys.argv[1], "w"), indent=1)
