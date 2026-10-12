#!/usr/bin/env python3
"""一次性调查第 2 步：NRT 说明、各分析中心最新的 EVEB/EVEC 坐标序列到哪天。只读 IGN 匿名 FTP。"""
import ftplib, io, json, gzip, re, subprocess, datetime as dt, sys
out = {"t": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z", "errors": []}
f = ftplib.FTP("doris.ign.fr", timeout=60); f.login()
def get(path):
    b = io.BytesIO(); f.retrbinary("RETR " + path, b.write); raw = b.getvalue()
    if path.endswith(".Z"): return subprocess.run(["uncompress", "-c"], input=raw, capture_output=True).stdout.decode("latin1", "replace")
    if path.endswith(".gz"): return gzip.decompress(raw).decode("latin1", "replace")
    return raw.decode("latin1", "replace")
out["readme_nrt"] = get("/pub/doris/data/README_rinexNRT.txt")[:4000]
try: out["doris_data_txt"] = get("/pub/doris/data/doris_data.txt")[:2500]
except Exception as e: out["errors"].append(repr(e))
# NRT 目录
for p in ("/pub/doris/data/ja3", "/pub/doris/data/s6a", "/pub/doris/data"):
    try: out.setdefault("ls", {})[p] = sorted(f.nlst(p))[-12:]
    except Exception as e: out["errors"].append(f"{p} {e!r}")
# STCD：所有目录里 eve* 文件，按目录名（含年份）排序取最新
dirs = sorted(f.nlst("/pub/doris/products/stcd"))
out["stcd_dirs_tail"] = dirs[-25:]
hits = []
for d in dirs:
    try:
        for n in f.nlst(d):
            b = n.rsplit("/", 1)[-1]
            if re.search(r"\.eve[bc]", b) and not b.endswith(".gif"): hits.append(d.rsplit("/", 1)[-1] + "/" + b)
    except Exception: pass
def yr(h):
    m = re.match(r"[a-z]{3}(\d\d)", h); return int(m.group(1)) if m else 0
hits.sort(key=lambda h: (yr(h), h))
out["stcd_eve_latest"] = hits[-12:]
res = {}
for h in hits[-6:]:
    try:
        lines = [l for l in get("/pub/doris/products/stcd/" + h).splitlines() if re.match(r"\s+\d{5}\.\d", l)]
        mjd = float(lines[-1].split()[0]); d = dt.date(1858, 11, 17) + dt.timedelta(days=int(mjd))
        res[h] = {"n": len(lines), "first_mjd": lines[0].split()[0], "last_mjd": mjd, "last_date": str(d), "last": lines[-1][:110]}
    except Exception as e: res[h] = {"err": repr(e)[:120]}
out["stcd_eve_series"] = res
f.quit()
json.dump(out, open(sys.argv[1], "w"), indent=1, ensure_ascii=False)
