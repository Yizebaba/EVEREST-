#!/usr/bin/env python3
"""一次性调查第 3 步：NRT 目录最新文件多新、里面有没有 EVEC、观测类型。只读 IGN 匿名 FTP。"""
import ftplib, io, json, gzip, re, subprocess, datetime as dt, sys
out = {"t": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z", "nrt": {}, "errors": []}
f = ftplib.FTP("doris.ign.fr", timeout=60); f.login()
def get(path):
    b = io.BytesIO(); f.retrbinary("RETR " + path, b.write); raw = b.getvalue()
    if path.endswith(".Z"): return subprocess.run(["uncompress", "-c"], input=raw, capture_output=True).stdout.decode("latin1", "replace"), len(raw)
    if path.endswith(".gz"): return gzip.decompress(raw).decode("latin1", "replace"), len(raw)
    return raw.decode("latin1", "replace"), len(raw)
for sat in ("ja3", "s6a", "s3a", "swo", "h2c", "srl"):
    try:
        base = f"/pub/doris/data/{sat}/NRT"
        names = sorted(n.rsplit("/", 1)[-1] for n in f.nlst(base))
        out.setdefault("ls", {})[sat] = names[-6:]
        sub = [n for n in names if re.fullmatch(r"\d{4}", n)]
        if sub:
            yd = base + "/" + sub[-1]; inner = sorted(n.rsplit("/", 1)[-1] for n in f.nlst(yd))
            dd = [n for n in inner if re.fullmatch(r"\d{3}", n)]
            out["ls"][sat + "_y"] = inner[-6:]
            if dd: yd = yd + "/" + dd[-1]; inner = sorted(n.rsplit("/", 1)[-1] for n in f.nlst(yd)); out["ls"][sat + "_d"] = inner[-6:]
            files = [yd + "/" + n for n in inner]
        else:
            files = [base + "/" + n for n in names]
        info = {"n": len(files), "newest": [x.rsplit("/", 1)[-1] for x in files[-2:]], "evec_passes": []}
        for fp in files[-10:]:
            txt, size = get(fp)
            head, _, body = txt.partition("END OF HEADER")
            if "obs_types" not in info:
                info["obs_types"] = [l[:60].strip() for l in head.splitlines() if "OBS TYPES" in l][:3]
                info["bytes"] = size
            ev = [l for l in head.splitlines() if "STATION REFERENCE" in l and "EVEC" in l]
            if not ev: continue
            sid = ev[0].split()[0]; cur = None; ep = []
            for l in body.splitlines():
                if l.startswith(">"): cur = l[2:21]
                elif l.startswith(sid): ep.append(cur)
            if ep: info["evec_passes"].append({"file": fp.rsplit("/", 1)[-1], "first": ep[0], "last": ep[-1], "n": len(ep),
                     "sample": next(l[:150] for l in body.splitlines() if l.startswith(sid))})
        out["nrt"][sat] = info
    except Exception as e:
        out["errors"].append(f"{sat}: {e!r}"[:200])
f.quit()
json.dump(out, open(sys.argv[1], "w"), indent=1, ensure_ascii=False)
